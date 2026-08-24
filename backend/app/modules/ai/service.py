from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.modules.ai.indexer import AiIndexer
from app.modules.ai.models import ContentEmbedding
from app.modules.ai.provider import OpenAiProvider
from app.modules.ai.repository import AiRepository, cosine_similarity, parse_embedding, serialize_embedding
from app.modules.ai.schemas import (
    AiChatResponse,
    AiIndexResponse,
    AiSourceItem,
    AiStatusResponse,
    CurrentSelectionResponse,
    ModelOptionResponse,
    UseCaseHistoryItem,
    UseCaseResponse,
)
from app.modules.ai.use_cases import (
    USE_CASE_DISPLAY_NAMES,
    default_option,
    is_valid_option,
    known_use_cases,
    options_for,
)


class AiService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.repo = AiRepository(db)
        self.provider = OpenAiProvider(self.settings)
        self.indexer = AiIndexer(db)

    async def _connected_providers(self, user_id: str) -> set[str]:
        """Providers the user has a configured credential for (Integrations)."""
        from app.modules.integrations.repository import IntegrationRepository
        from app.modules.integrations.sarvam_config import parse_config as parse_sarvam_config

        connected: set[str] = set()
        repo = IntegrationRepository(self.db)
        sarvam = await repo.get_by_provider(user_id, "sarvam")
        if sarvam is not None and parse_sarvam_config(sarvam.config_json) is not None:
            connected.add("sarvam")
        return connected

    async def list_use_cases(self, user_id: str) -> list[UseCaseResponse]:
        connected = await self._connected_providers(user_id)
        selections = {s.use_case: s for s in await self.repo.list_selections(user_id)}
        result: list[UseCaseResponse] = []
        for use_case in known_use_cases():
            opts = [
                ModelOptionResponse(
                    provider=o.provider,
                    model=o.model,
                    display_name=o.display_name,
                    available=o.provider in connected,
                )
                for o in options_for(use_case)
            ]
            current = None
            sel = selections.get(use_case)
            if sel is not None:
                current = CurrentSelectionResponse(
                    provider=sel.provider,
                    model=sel.model,
                    updated_at=sel.updated_at,
                )
            else:
                default = default_option(use_case)
                if default is not None and default.provider in connected:
                    current = CurrentSelectionResponse(
                        provider=default.provider,
                        model=default.model,
                        updated_at=None,
                    )
            result.append(
                UseCaseResponse(
                    use_case=use_case,
                    display_name=USE_CASE_DISPLAY_NAMES.get(use_case, use_case),
                    options=opts,
                    current=current,
                )
            )
        return result

    async def set_use_case_model(
        self, user_id: str, use_case: str, provider: str, model: str
    ) -> UseCaseResponse:
        if use_case not in known_use_cases():
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown use case: {use_case}")
        if not is_valid_option(use_case, provider, model):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Model {provider}:{model} is not allowed for {use_case}",
            )
        connected = await self._connected_providers(user_id)
        if provider not in connected:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Connect your {provider} API key in Integrations before selecting this model",
            )
        await self.repo.set_selection(user_id, use_case, provider, model)
        items = await self.list_use_cases(user_id)
        return next(i for i in items if i.use_case == use_case)

    async def get_use_case_history(
        self, user_id: str, use_case: str
    ) -> list[UseCaseHistoryItem]:
        if use_case not in known_use_cases():
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown use case: {use_case}")
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

    async def resolve_model_for_use_case(
        self, user_id: str, use_case: str
    ) -> tuple[str, str]:
        """Return (provider, model) for the next AI call on this use case."""
        sel = await self.repo.get_selection(user_id, use_case)
        if sel is not None:
            return sel.provider, sel.model
        default = default_option(use_case)
        if default is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"No model configured for use case {use_case}",
            )
        return default.provider, default.model

    async def status(self, user_id: str) -> AiStatusResponse:
        total, embedded = await self.repo.count_for_user(user_id)
        return AiStatusResponse(
            enabled=self.provider.enabled,
            provider="openai" if self.provider.enabled else "none",
            indexed_chunks=total,
            embedding_chunks=embedded,
        )

    async def index(self, user_id: str) -> AiIndexResponse:
        await self.repo.clear_user_index(user_id)
        docs = await self.indexer.collect_documents(user_id)
        embedded = 0
        for doc in docs:
            embedding_json = None
            if self.provider.enabled and doc.content.strip():
                try:
                    vec = await self.provider.embed(doc.content[:8000])
                    embedding_json = serialize_embedding(vec)
                    embedded += 1
                except Exception:
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

    async def chat(self, user_id: str, message: str) -> AiChatResponse:
        rows = await self.repo.list_for_user(user_id)
        if not rows:
            await self.index(user_id)
            rows = await self.repo.list_for_user(user_id)

        sources = await self._retrieve(user_id, message, rows)
        context = "\n\n".join(
            f"[{s.source_type}] {s.title}: {s.snippet}" for s in sources[:8]
        ) or "No personal records matched this question yet."

        if self.provider.enabled:
            system = (
                "You are LifeOS, a personal AI assistant. Answer using ONLY the personal context below. "
                "If context is insufficient, say what is missing. Be concise and actionable.\n\n"
                f"Personal context:\n{context}"
            )
            try:
                reply = await self.provider.chat(system, message)
            except Exception as exc:
                reply = f"I found relevant records but could not reach the AI provider: {exc}"
        else:
            reply = (
                "AI provider is not configured (set OPENAI_API_KEY in backend/.env). "
                "Here is what I found in your LifeOS data:\n\n" + context
            )

        return AiChatResponse(reply=reply, sources=sources[:8])

    async def _retrieve(
        self, user_id: str, query: str, rows: list[ContentEmbedding]
    ) -> list[AiSourceItem]:
        q = query.lower()
        scored: list[AiSourceItem] = []

        query_vec: list[float] | None = None
        if self.provider.enabled:
            try:
                query_vec = await self.provider.embed(query)
            except Exception:
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

        if self.provider.enabled:
            system = (
                "Extract a task from the user message. Reply with ONLY JSON: "
                '{"title": "...", "due": "YYYY-MM-DD|today|tomorrow|null"}. '
                "No markdown."
            )
            try:
                raw = await self.provider.chat(system, natural_language)
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
            except Exception:
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
