import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.ai.adapters.base import AiProviderError, MissingCredentialError
from app.modules.ai.adapters.registry import AI_PROVIDERS, is_ai_provider, provider_label
from app.modules.ai.gateway import AiGateway
from app.modules.ai.indexer import AiIndexer
from app.modules.ai.models import AIProviderModel, ContentEmbedding
from app.modules.ai.repository import AiRepository, cosine_similarity, parse_embedding, serialize_embedding
from app.modules.ai.schemas import (
    AiChatResponse,
    AiIndexResponse,
    AiSettings,
    AiSourceItem,
    AiStatusResponse,
    CurrentSelectionResponse,
    ModelOptionResponse,
    UseCaseHistoryItem,
    UseCaseResponse,
)
from app.modules.ai.use_cases import USE_CASE_RAG_CHAT, USE_CASES, UseCase, get_use_case

logger = logging.getLogger(__name__)

EMBED_INPUT_MAX_CHARS = 8000
OFFLINE_HINT = "Connect an AI provider in Integrations → AI (or set OPENAI_API_KEY in backend/.env)."


def _option(row: AIProviderModel) -> ModelOptionResponse:
    return ModelOptionResponse(
        provider=row.provider,
        model=row.model_id,
        display_name=f"{provider_label(row.provider)} · {row.display_name}",
    )


class AiService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.repo = AiRepository(db)
        self.gateway = AiGateway(db, self.settings)
        self.indexer = AiIndexer(db)

    async def _connected_providers(self, user_id: str) -> set[str]:
        """Providers with usable credentials (enabled BYOK, or env for OpenAI)."""
        return {p for p in AI_PROVIDERS if await self.gateway.credentials(user_id, p) is not None}

    async def _use_case_response(
        self, user_id: str, uc: UseCase, connected: set[str], models: list[AIProviderModel]
    ) -> UseCaseResponse:
        options = [
            _option(m) for m in models if m.provider in connected and uc.capability in m.capability_set
        ]
        current = None
        sel = await self.repo.get_selection(user_id, uc.id)
        if sel is not None:
            current = CurrentSelectionResponse(
                provider=sel.provider,
                model=sel.model,
                updated_at=sel.updated_at,
                available=sel.provider in connected,
            )
        else:
            try:
                resolved = await self.gateway.resolve(user_id, uc.id)
                current = CurrentSelectionResponse(provider=resolved.provider, model=resolved.model)
            except MissingCredentialError:
                current = None
        return UseCaseResponse(
            use_case=uc.id,
            display_name=uc.display_name,
            capability=uc.capability,
            options=options,
            current=current,
        )

    async def list_use_cases(self, user_id: str) -> list[UseCaseResponse]:
        connected = await self._connected_providers(user_id)
        models = await self.repo.list_models(user_id)
        return [await self._use_case_response(user_id, uc, connected, models) for uc in USE_CASES.values()]

    async def set_use_case_model(
        self, user_id: str, use_case: str, provider: str, model: str, *, custom: bool = False
    ) -> UseCaseResponse:
        uc = get_use_case(use_case)
        if uc is None:
            raise NotFoundError(f"Unknown use case: {use_case}")
        if not is_ai_provider(provider):
            raise BadRequestError(f"Unknown AI provider: {provider}")
        connected = await self._connected_providers(user_id)
        if provider not in connected:
            raise BadRequestError(
                f"Connect your {provider_label(provider)} API key in Integrations before selecting this model"
            )
        models = await self.repo.list_models(user_id)
        if not custom and not any(
            m.provider == provider and m.model_id == model and uc.capability in m.capability_set
            for m in models
        ):
            raise BadRequestError(
                f"Model {provider}:{model} is not in the cached model list for {uc.display_name}. "
                "Refresh models or use a custom model id."
            )
        await self.repo.set_selection(user_id, use_case, provider, model)
        return await self._use_case_response(user_id, uc, connected, models)

    async def clear_use_case_model(self, user_id: str, use_case: str) -> UseCaseResponse:
        uc = get_use_case(use_case)
        if uc is None:
            raise NotFoundError(f"Unknown use case: {use_case}")
        await self.repo.clear_selection(user_id, use_case)
        connected = await self._connected_providers(user_id)
        return await self._use_case_response(user_id, uc, connected, await self.repo.list_models(user_id))

    async def get_use_case_history(
        self, user_id: str, use_case: str
    ) -> list[UseCaseHistoryItem]:
        if get_use_case(use_case) is None:
            raise NotFoundError(f"Unknown use case: {use_case}")
        rows = await self.repo.list_history(user_id, use_case)
        return [
            UseCaseHistoryItem(
                provider=r.provider,
                model=r.model,
                effective_from=r.effective_from,
                effective_to=r.effective_to,
            )
            for r in rows
        ]

    async def get_ai_settings(self, user_id: str) -> AiSettings:
        return await self.repo.get_ai_settings(user_id)

    async def save_ai_settings(self, user_id: str, data: AiSettings) -> AiSettings:
        if data.default_provider is not None and not is_ai_provider(data.default_provider):
            raise BadRequestError(f"Unknown AI provider: {data.default_provider}")
        return await self.repo.put_ai_settings(user_id, data)

    async def status(self, user_id: str) -> AiStatusResponse:
        total, embedded = await self.repo.count_for_user(user_id)
        try:
            provider = (await self.gateway.resolve(user_id, USE_CASE_RAG_CHAT)).provider
        except MissingCredentialError:
            provider = None
        return AiStatusResponse(
            enabled=provider is not None,
            provider=provider or "none",
            indexed_chunks=total,
            embedding_chunks=embedded,
        )

    async def index(self, user_id: str) -> AiIndexResponse:
        await self.repo.clear_user_index(user_id)
        docs = await self.indexer.collect_documents(user_id)
        embedder = await self.gateway.embedding_adapter(user_id)
        embedded = 0
        for doc in docs:
            embedding_json = None
            if embedder is not None and doc.content.strip():
                adapter, model = embedder
                try:
                    vec = await adapter.embed(doc.content[:EMBED_INPUT_MAX_CHARS], model=model)
                    embedding_json = serialize_embedding(vec)
                    embedded += 1
                except AiProviderError:
                    embedding_json = None
            await self.repo.upsert_chunk(
                ContentEmbedding(
                    user_id=user_id,
                    source_type=doc.source_type,
                    source_id=doc.source_id,
                    title=doc.title,
                    content=doc.content,
                    route=doc.route,
                    embedding_json=embedding_json,
                )
            )
        return AiIndexResponse(indexed=len(docs), embedded=embedded)

    async def chat(
        self, user_id: str, message: str, *, use_case: str = USE_CASE_RAG_CHAT
    ) -> AiChatResponse:
        rows = await self.repo.list_for_user(user_id)
        if not rows:
            await self.index(user_id)
            rows = await self.repo.list_for_user(user_id)

        sources = await self._retrieve(user_id, message, rows)
        context = "\n\n".join(
            f"[{s.source_type}] {s.title}: {s.snippet}" for s in sources[:8]
        ) or "No personal records matched this question yet."

        system = (
            "You are LifeOS, a personal AI assistant. Answer using ONLY the personal context below. "
            "If context is insufficient, say what is missing. Be concise and actionable.\n\n"
            f"Personal context:\n{context}"
        )
        try:
            reply = await self.gateway.chat(user_id, use_case, system, message)
        except MissingCredentialError:
            reply = (
                f"AI provider is not configured. {OFFLINE_HINT} "
                "Here is what I found in your LifeOS data:\n\n" + context
            )
        except AiProviderError:
            logger.exception("AI chat provider failed use_case=%s", use_case)
            reply = (
                "I found relevant records but could not reach the AI provider. "
                "Please try again shortly."
            )

        return AiChatResponse(reply=reply, sources=sources[:8])

    async def _retrieve(
        self, user_id: str, query: str, rows: list[ContentEmbedding]
    ) -> list[AiSourceItem]:
        q = query.lower()
        scored: list[AiSourceItem] = []

        query_vec: list[float] | None = None
        embedder = await self.gateway.embedding_adapter(user_id)
        if embedder is not None:
            adapter, model = embedder
            try:
                query_vec = await adapter.embed(query, model=model)
            except AiProviderError:
                query_vec = None

        for row in rows:
            keyword_score = 0.0
            hay = f"{row.title} {row.content}".lower()
            for token in q.split():
                if len(token) >= 2 and token in hay:
                    keyword_score += 1.0

            vector_score = 0.0
            if query_vec:
                emb = parse_embedding(row.embedding_json)
                if emb:
                    vector_score = cosine_similarity(query_vec, emb)

            score = vector_score * 10 + keyword_score
            if score <= 0:
                continue
            snippet = row.content[:240] + ("…" if len(row.content) > 240 else "")
            scored.append(
                AiSourceItem(
                    source_type=row.source_type,
                    source_id=row.source_id,
                    title=row.title,
                    route=row.route,
                    snippet=snippet,
                    score=round(score, 3),
                )
            )

        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:12]

    async def suggest_task_breakdown(self, user_id: str, task_text: str) -> str:
        """Ask the AI to break a task into concrete sub-steps. Telegram only displays the result."""
        prompt = (
            "Break the following task into a short numbered list of concrete sub-steps "
            "(max 8). Be practical and concise.\n\n"
            f"Task: {task_text}"
        )
        chat = await self.chat(user_id, prompt)
        return chat.reply

    async def parse_and_create_task(self, user_id: str, natural_language: str):
        """Parse free-text into a structured task and create it via TaskService.

        Uses the AI provider when available; falls back to regex title + due today.
        Returns TaskResponse or None.
        """
        import json
        import re
        from datetime import date, datetime, time, timedelta, timezone

        from app.modules.tasks.schemas import TaskCreate
        from app.modules.tasks.service import TaskService

        title = natural_language.strip()[:200]
        due: datetime | None = datetime.combine(
            date.today(), time(12, 0), tzinfo=timezone.utc
        )

        system = (
            "Extract a task from the user message. Reply with ONLY JSON: "
            '{"title": "...", "due": "YYYY-MM-DD|today|tomorrow|null"}. '
            "No markdown."
        )
        raw: str | None
        try:
            raw = await self.gateway.chat(user_id, USE_CASE_RAG_CHAT, system, natural_language)
        except MissingCredentialError:
            raw = None
        except AiProviderError:
            # Provider failed: keep the raw text as the title rather than guessing.
            raw = ""

        if raw is not None:
            try:
                m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    title = str(data.get("title") or title).strip()[:200]
                    due_token = data.get("due")
                    if due_token in (None, "null", ""):
                        due = datetime.combine(
                            date.today(), time(12, 0), tzinfo=timezone.utc
                        )
                    elif str(due_token).lower() == "today":
                        due = datetime.combine(
                            date.today(), time(12, 0), tzinfo=timezone.utc
                        )
                    elif str(due_token).lower() == "tomorrow":
                        due = datetime.combine(
                            date.today() + timedelta(days=1),
                            time(12, 0),
                            tzinfo=timezone.utc,
                        )
                    else:
                        try:
                            due = datetime.combine(
                                date.fromisoformat(str(due_token)[:10]),
                                time(12, 0),
                                tzinfo=timezone.utc,
                            )
                        except ValueError:
                            pass
            except ValueError:
                # Unparseable JSON from the model: keep the raw title.
                pass
        else:
            # Lightweight fallback: strip leading verbs / "remind me to"
            cleaned = re.sub(
                r"^(remind me to|please |add task |todo[:\s]*)",
                "",
                natural_language.strip(),
                flags=re.IGNORECASE,
            ).strip()
            if cleaned:
                title = cleaned[:200]

        if not title:
            return None
        return await TaskService(self.db).create_task(
            user_id, TaskCreate(title=title, due_date=due)
        )
