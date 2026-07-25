from app.core.config import Settings, get_settings
from app.modules.ai.indexer import AiIndexer
from app.modules.ai.models import ContentEmbedding
from app.modules.ai.provider import OpenAiProvider
from app.modules.ai.repository import AiRepository, cosine_similarity, parse_embedding, serialize_embedding
from app.modules.ai.schemas import AiChatResponse, AiIndexResponse, AiSourceItem, AiStatusResponse
from sqlalchemy.ext.asyncio import AsyncSession


class AiService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.repo = AiRepository(db)
        self.provider = OpenAiProvider(self.settings)
        self.indexer = AiIndexer(db)

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
