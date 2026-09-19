import hashlib
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppError,
    BadGatewayError,
    BadRequestError,
    ServiceUnavailableError,
    UnauthorizedError,
    get_or_404,
)
from app.modules.ai.service import AiService
from app.modules.ai.use_cases import USE_CASE_WRITING_FEEDBACK
from app.modules.communication.ai.metrics import compute_deterministic_metrics
from app.modules.communication.ai.provider import (
    InvalidCredentialError,
    MalformedResponseError,
    MissingCredentialError,
    ProviderUnavailableError,
    RateLimitError,
    SarvamWritingProvider,
    TimeoutError_,
    WritingAiError,
)
from app.modules.communication.ai.rubric import (
    EVALUATION_VERSION,
    PROMPT_VERSION,
    REWRITE_PROMPT_VERSION,
    RUBRIC_VERSION,
)
from app.modules.communication.models import (
    WRITING_CATEGORIES,
    WritingAIRun,
    WritingEvaluation,
    WritingRewritePreview,
    dumps_json,
    loads_json,
)
from app.modules.communication.repository import CommunicationRepository
from app.modules.communication.schemas import (
    SpeakingCreate,
    SpeakingResponse,
    SpeakingUpdate,
    WritingCreate,
    WritingEvaluationResponse,
    WritingIssueItem,
    WritingResponse,
    WritingRewriteResponse,
    WritingUpdate,
)
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.sarvam_config import parse_config as parse_sarvam_config


def _writing_ai_error(exc: WritingAiError) -> AppError:
    detail = {"code": exc.code, "message": str(exc)}
    if isinstance(exc, (TimeoutError_, ProviderUnavailableError, RateLimitError)):
        return ServiceUnavailableError(detail)
    if isinstance(exc, InvalidCredentialError):
        return UnauthorizedError(detail)
    if isinstance(exc, MissingCredentialError):
        return BadRequestError(detail)
    if isinstance(exc, MalformedResponseError):
        return BadGatewayError(detail)
    return BadRequestError(detail)

def _evaluation_key(
    *,
    content: str,
    rubric_version: str,
    prompt_version: str,
    evaluation_version: str,
    provider: str,
    model: str,
) -> str:
    payload = "\n".join(
        [
            hashlib.sha256(content.encode("utf-8")).hexdigest(),
            rubric_version,
            prompt_version,
            evaluation_version,
            provider,
            model,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _rewrite_key(
    *,
    content: str,
    prompt_version: str,
    provider: str,
    model: str,
) -> str:
    payload = "\n".join(
        [
            hashlib.sha256(content.encode("utf-8")).hexdigest(),
            prompt_version,
            provider,
            model,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _to_evaluation_response(row: WritingEvaluation, *, cached: bool = False) -> WritingEvaluationResponse:
    issues_raw = loads_json(row.issues_json, [])
    issues = [WritingIssueItem.model_validate(i) for i in issues_raw if isinstance(i, dict)]
    return WritingEvaluationResponse(
        id=row.id,
        writing_id=row.writing_id,
        evaluation_key=row.evaluation_key,
        provider=row.provider,
        model=row.model,
        model_version=row.model_version,
        prompt_version=row.prompt_version,
        rubric_version=row.rubric_version,
        evaluation_version=row.evaluation_version,
        overall_score=row.overall_score,
        dimensions=loads_json(row.dimensions_json, {}),
        strengths=loads_json(row.strengths_json, []),
        issues=issues,
        suggestions=loads_json(row.suggestions_json, []),
        metrics=loads_json(row.metrics_json, {}),
        already_strong=row.already_strong,
        truncated=row.truncated,
        truncation_note=row.truncation_note,
        cached=cached,
        created_at=row.created_at,
    )

def _to_rewrite_response(row: WritingRewritePreview, *, cached: bool = False) -> WritingRewriteResponse:
    return WritingRewriteResponse(
        id=row.id,
        writing_id=row.writing_id,
        rewrite_key=row.rewrite_key,
        provider=row.provider,
        model=row.model,
        prompt_version=row.prompt_version,
        suggested_text=row.suggested_text,
        why_better=loads_json(row.why_better_json, []),
        key_changes=loads_json(row.key_changes_json, []),
        truncated=row.truncated,
        truncation_note=row.truncation_note,
        cached=cached,
        created_at=row.created_at,
    )

class CommunicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CommunicationRepository(db)

    async def list_writing(
        self, user_id: str, category: str | None = None, limit: int = 25, offset: int = 0
    ) -> tuple[list[WritingResponse], int]:
        items, total = await self.repo.list_writing(
            user_id, category=category, limit=limit, offset=offset
        )
        return [WritingResponse.model_validate(i) for i in items], total

    async def list_writing_categories(self, user_id: str) -> list[str]:
        stored = await self.repo.list_category_names(user_id)
        used = await self.repo.list_used_category_names(user_id)
        seen: dict[str, str] = {}
        for name in [*WRITING_CATEGORIES, *stored, *used]:
            key = name.strip().lower()
            if key and key not in seen:
                seen[key] = name.strip()
        return sorted(seen.values(), key=str.lower)

    async def create_writing_category(self, user_id: str, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise BadRequestError("Category name required")
        await self.repo.ensure_category(user_id, clean)
        return clean

    async def get_writing(self, user_id: str, item_id: str) -> WritingResponse:
        item = get_or_404(await self.repo.get_writing(user_id, item_id), "Writing not found")
        return WritingResponse.model_validate(item)

    async def create_writing(self, user_id: str, data: WritingCreate) -> WritingResponse:
        item = await self.repo.create_writing(user_id, data)
        return WritingResponse.model_validate(item)

    async def update_writing(self, user_id: str, item_id: str, data: WritingUpdate) -> WritingResponse:
        item = get_or_404(await self.repo.get_writing(user_id, item_id), "Writing not found")
        updated = await self.repo.update_writing(item, data)
        return WritingResponse.model_validate(updated)

    async def delete_writing(self, user_id: str, item_id: str) -> None:
        item = get_or_404(await self.repo.get_writing(user_id, item_id), "Writing not found")
        await self.repo.delete_writing(item)

    async def list_speaking(
        self, user_id: str, category: str | None = None, limit: int = 25, offset: int = 0
    ) -> tuple[list[SpeakingResponse], int]:
        items, total = await self.repo.list_speaking(
            user_id, category=category, limit=limit, offset=offset
        )
        return [SpeakingResponse.model_validate(i) for i in items], total

    async def get_speaking(self, user_id: str, item_id: str) -> SpeakingResponse:
        item = get_or_404(await self.repo.get_speaking(user_id, item_id), "Speaking practice not found")
        return SpeakingResponse.model_validate(item)

    async def create_speaking(self, user_id: str, data: SpeakingCreate) -> SpeakingResponse:
        item = await self.repo.create_speaking(user_id, data)
        return SpeakingResponse.model_validate(item)

    async def update_speaking(self, user_id: str, item_id: str, data: SpeakingUpdate) -> SpeakingResponse:
        item = get_or_404(await self.repo.get_speaking(user_id, item_id), "Speaking practice not found")
        updated = await self.repo.update_speaking(item, data)
        return SpeakingResponse.model_validate(updated)

    async def delete_speaking(self, user_id: str, item_id: str) -> None:
        item = get_or_404(await self.repo.get_speaking(user_id, item_id), "Speaking practice not found")
        await self.repo.delete_speaking(item)

    async def get_writing_feedback(
        self, user_id: str, writing_id: str
    ) -> WritingEvaluationResponse:
        get_or_404(await self.repo.get_writing(user_id, writing_id), "Writing not found")
        latest = get_or_404(await self.repo.get_latest_evaluation(user_id, writing_id), "No AI feedback yet. Click AI Feedback to evaluate this writing.",)
        return _to_evaluation_response(latest, cached=True)

    async def evaluate_writing(self, user_id: str, writing_id: str) -> WritingEvaluationResponse:
        item = get_or_404(await self.repo.get_writing(user_id, writing_id), "Writing not found")
        if not (item.content or "").strip():
            raise BadRequestError("Write some content before requesting AI Feedback.",)

        provider_name, model = await AiService(self.db).resolve_model_for_use_case(
            user_id, USE_CASE_WRITING_FEEDBACK
        )
        if provider_name != "sarvam":
            raise BadRequestError(f"Provider '{provider_name}' is not implemented for writing feedback yet.",)

        key = _evaluation_key(
            content=item.content or "",
            rubric_version=RUBRIC_VERSION,
            prompt_version=PROMPT_VERSION,
            evaluation_version=EVALUATION_VERSION,
            provider=provider_name,
            model=model,
        )
        existing = await self.repo.get_evaluation_by_key(writing_id, key)
        if existing is not None:
            return _to_evaluation_response(existing, cached=True)

        conn = await IntegrationRepository(self.db).get_by_provider(user_id, "sarvam")
        cfg = parse_sarvam_config(conn.config_json) if conn is not None else None
        if cfg is None:
            raise BadRequestError({
                    "code": "missing_credential",
                    "message": "Connect your Sarvam API key in Integrations before requesting AI Feedback.",
                },)

        run = WritingAIRun(
            user_id=user_id,
            writing_id=writing_id,
            provider=provider_name,
            model=model,
            operation="evaluate_writing",
            prompt_version=PROMPT_VERSION,
            rubric_version=RUBRIC_VERSION,
            status="pending",
        )
        await self.repo.create_ai_run(run)

        adapter = SarvamWritingProvider(api_key=cfg.api_key, model=model)
        started = time.perf_counter()
        try:
            result = await adapter.evaluate_writing(
                title=item.title,
                content=item.content or "",
                category=item.category,
            )
        except WritingAiError as exc:
            run.status = "error"
            run.error_code = exc.code
            run.error_message = str(exc)
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            await self.repo.update_ai_run(run)
            raise _writing_ai_error(exc) from exc
        except Exception as exc:
            run.status = "error"
            run.error_code = "unknown"
            run.error_message = str(exc)
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            await self.repo.update_ai_run(run)
            raise ServiceUnavailableError({
                    "code": "provider_unavailable",
                    "message": "AI feedback is temporarily unavailable. Your writing has not been changed.",
                }) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        usage = result.pop("_usage", {}) or {}
        metrics = compute_deterministic_metrics(item.content or "")

        evaluation = WritingEvaluation(
            user_id=user_id,
            writing_id=writing_id,
            evaluation_key=key,
            provider=result["provider"],
            model=result["model"],
            model_version=None,
            prompt_version=result.get("promptVersion", PROMPT_VERSION),
            rubric_version=result.get("rubricVersion", RUBRIC_VERSION),
            evaluation_version=result.get("evaluationVersion", EVALUATION_VERSION),
            overall_score=int(result["overallScore"]),
            dimensions_json=dumps_json(result.get("dimensions") or {}),
            strengths_json=dumps_json(result.get("strengths") or []),
            issues_json=dumps_json(result.get("issues") or []),
            suggestions_json=dumps_json(result.get("suggestions") or []),
            metrics_json=dumps_json(metrics),
            already_strong=bool(result.get("alreadyStrong")),
            truncated=bool(result.get("truncated")),
            truncation_note=result.get("truncationNote"),
        )
        try:
            saved = await self.repo.create_evaluation(evaluation)
        except Exception:
            # Race: another request may have inserted the same key.
            raced = await self.repo.get_evaluation_by_key(writing_id, key)
            if raced is not None:
                run.status = "cached"
                run.latency_ms = latency_ms
                await self.repo.update_ai_run(run)
                return _to_evaluation_response(raced, cached=True)
            raise

        run.status = "success"
        run.latency_ms = latency_ms
        run.prompt_tokens = usage.get("prompt_tokens")
        run.completion_tokens = usage.get("completion_tokens")
        await self.repo.update_ai_run(run)

        return _to_evaluation_response(saved, cached=False)

    async def get_writing_rewrite(self, user_id: str, writing_id: str) -> WritingRewriteResponse:
        get_or_404(await self.repo.get_writing(user_id, writing_id), "Writing not found")
        latest = get_or_404(await self.repo.get_latest_rewrite(user_id, writing_id), "No coach rewrite yet. Click “How AI would write this” to generate one.",)
        return _to_rewrite_response(latest, cached=True)

    async def request_writing_rewrite(self, user_id: str, writing_id: str) -> WritingRewriteResponse:
        item = get_or_404(await self.repo.get_writing(user_id, writing_id), "Writing not found")
        if not (item.content or "").strip():
            raise BadRequestError("Write some content before requesting a coach rewrite.",)

        provider_name, model = await AiService(self.db).resolve_model_for_use_case(
            user_id, USE_CASE_WRITING_FEEDBACK
        )
        if provider_name != "sarvam":
            raise BadRequestError(f"Provider '{provider_name}' is not implemented for writing rewrite yet.",)

        key = _rewrite_key(
            content=item.content or "",
            prompt_version=REWRITE_PROMPT_VERSION,
            provider=provider_name,
            model=model,
        )
        existing = await self.repo.get_rewrite_by_key(writing_id, key)
        if existing is not None:
            return _to_rewrite_response(existing, cached=True)

        conn = await IntegrationRepository(self.db).get_by_provider(user_id, "sarvam")
        cfg = parse_sarvam_config(conn.config_json) if conn is not None else None
        if cfg is None:
            raise BadRequestError({
                    "code": "missing_credential",
                    "message": "Connect your Sarvam API key in Integrations before requesting a coach rewrite.",
                },)

        run = WritingAIRun(
            user_id=user_id,
            writing_id=writing_id,
            provider=provider_name,
            model=model,
            operation="suggest_rewrite",
            prompt_version=REWRITE_PROMPT_VERSION,
            rubric_version=RUBRIC_VERSION,
            status="pending",
        )
        await self.repo.create_ai_run(run)

        adapter = SarvamWritingProvider(api_key=cfg.api_key, model=model)
        started = time.perf_counter()
        try:
            result = await adapter.suggest_rewrite(
                title=item.title,
                content=item.content or "",
                category=item.category,
            )
        except WritingAiError as exc:
            run.status = "error"
            run.error_code = exc.code
            run.error_message = str(exc)
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            await self.repo.update_ai_run(run)
            raise _writing_ai_error(exc) from exc
        except Exception as exc:
            run.status = "error"
            run.error_code = "unknown"
            run.error_message = str(exc)
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            await self.repo.update_ai_run(run)
            raise ServiceUnavailableError({
                    "code": "provider_unavailable",
                    "message": "Coach rewrite is temporarily unavailable. Your writing has not been changed.",
                }) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        usage = result.pop("_usage", {}) or {}

        preview = WritingRewritePreview(
            user_id=user_id,
            writing_id=writing_id,
            rewrite_key=key,
            provider=result["provider"],
            model=result["model"],
            prompt_version=result.get("promptVersion", REWRITE_PROMPT_VERSION),
            suggested_text=result["suggestedVersion"],
            why_better_json=dumps_json(result.get("whyBetter") or []),
            key_changes_json=dumps_json(result.get("keyChanges") or []),
            truncated=bool(result.get("truncated")),
            truncation_note=result.get("truncationNote"),
        )
        try:
            saved = await self.repo.create_rewrite(preview)
        except Exception:
            raced = await self.repo.get_rewrite_by_key(writing_id, key)
            if raced is not None:
                run.status = "cached"
                run.latency_ms = latency_ms
                await self.repo.update_ai_run(run)
                return _to_rewrite_response(raced, cached=True)
            raise

        run.status = "success"
        run.latency_ms = latency_ms
        run.prompt_tokens = usage.get("prompt_tokens")
        run.completion_tokens = usage.get("completion_tokens")
        await self.repo.update_ai_run(run)

        return _to_rewrite_response(saved, cached=False)
