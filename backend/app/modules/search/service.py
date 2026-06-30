from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarEvent
from app.modules.communication.models import SpeakingPractice, VocabularyWord, WritingPractice
from app.modules.goals.models import Goal
from app.modules.habits.models import Habit
from app.modules.journal.models import JournalEntry
from app.modules.qa.models import QAEntry
from app.modules.running.models import Run
from app.modules.ai.service import AiService
from app.modules.search.schemas import SearchResponse, SearchResultItem
from app.modules.tasks.models import Task
from app.modules.wishlist.models import WishlistItem


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, user_id: str, query: str, limit: int = 20) -> SearchResponse:
        q = query.strip()
        if not q:
            return SearchResponse(query=q, total=0, results=[])
        pattern = f"%{q}%"
        results: list[SearchResultItem] = []

        async def add_goal_rows():
            rows = await self.db.execute(
                select(Goal).where(
                    Goal.user_id == user_id,
                    or_(Goal.title.ilike(pattern), Goal.description.ilike(pattern)),
                ).limit(limit)
            )
            for g in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="goals",
                        entity_type="goal",
                        id=g.id,
                        title=g.title,
                        subtitle=g.category,
                        route=f"/goals/{g.id}",
                    )
                )

        async def add_task_rows():
            rows = await self.db.execute(
                select(Task).where(
                    Task.user_id == user_id,
                    or_(Task.title.ilike(pattern), Task.description.ilike(pattern)),
                ).limit(limit)
            )
            for t in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="tasks",
                        entity_type="task",
                        id=t.id,
                        title=t.title,
                        subtitle=t.status,
                        route=f"/tasks/{t.id}",
                    )
                )

        async def add_habit_rows():
            rows = await self.db.execute(
                select(Habit).where(
                    Habit.user_id == user_id,
                    or_(Habit.name.ilike(pattern), Habit.description.ilike(pattern)),
                ).limit(limit)
            )
            for h in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="habits",
                        entity_type="habit",
                        id=h.id,
                        title=h.name,
                        subtitle=h.frequency,
                        route=f"/habits/{h.id}",
                    )
                )

        async def add_run_rows():
            rows = await self.db.execute(
                select(Run).where(Run.user_id == user_id, Run.notes.ilike(pattern)).limit(limit)
            )
            for r in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="running",
                        entity_type="run",
                        id=r.id,
                        title=f"{r.distance_km} km run",
                        subtitle=str(r.run_date),
                        route=f"/running/{r.id}",
                    )
                )

        async def add_calendar_rows():
            rows = await self.db.execute(
                select(CalendarEvent).where(
                    CalendarEvent.user_id == user_id,
                    or_(CalendarEvent.title.ilike(pattern), CalendarEvent.description.ilike(pattern)),
                ).limit(limit)
            )
            for e in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="calendar",
                        entity_type="event",
                        id=e.id,
                        title=e.title,
                        subtitle=e.category,
                        route=f"/calendar/{e.id}",
                    )
                )

        async def add_journal_rows():
            rows = await self.db.execute(
                select(JournalEntry).where(
                    JournalEntry.user_id == user_id,
                    or_(
                        JournalEntry.title.ilike(pattern),
                        JournalEntry.content.ilike(pattern),
                        JournalEntry.gratitude.ilike(pattern),
                    ),
                ).limit(limit)
            )
            for j in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="journal",
                        entity_type="entry",
                        id=j.id,
                        title=j.title or j.entry_type,
                        subtitle=str(j.entry_date),
                        route=f"/journal/{j.id}",
                    )
                )

        async def add_vocab_rows():
            rows = await self.db.execute(
                select(VocabularyWord).where(
                    VocabularyWord.user_id == user_id,
                    or_(VocabularyWord.word.ilike(pattern), VocabularyWord.meaning.ilike(pattern)),
                ).limit(limit)
            )
            for w in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="communication",
                        entity_type="vocabulary",
                        id=w.id,
                        title=w.word,
                        subtitle=w.meaning[:80] if w.meaning else None,
                        route=f"/communication/vocabulary/{w.id}",
                    )
                )

        async def add_writing_rows():
            rows = await self.db.execute(
                select(WritingPractice).where(
                    WritingPractice.user_id == user_id,
                    or_(WritingPractice.title.ilike(pattern), WritingPractice.content.ilike(pattern)),
                ).limit(limit)
            )
            for w in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="communication",
                        entity_type="writing",
                        id=w.id,
                        title=w.title,
                        subtitle=w.category,
                        route=f"/communication/writing/{w.id}",
                    )
                )

        async def add_speaking_rows():
            rows = await self.db.execute(
                select(SpeakingPractice).where(
                    SpeakingPractice.user_id == user_id,
                    or_(SpeakingPractice.title.ilike(pattern), SpeakingPractice.prompt.ilike(pattern)),
                ).limit(limit)
            )
            for s in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="communication",
                        entity_type="speaking",
                        id=s.id,
                        title=s.title,
                        subtitle=s.category,
                        route=f"/communication/speaking/{s.id}",
                    )
                )

        async def add_qa_rows():
            rows = await self.db.execute(
                select(QAEntry).where(
                    QAEntry.user_id == user_id,
                    or_(QAEntry.question.ilike(pattern), QAEntry.current_answer.ilike(pattern)),
                ).limit(limit)
            )
            for e in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="qa",
                        entity_type="entry",
                        id=e.id,
                        title=e.question,
                        subtitle=e.current_answer[:80] if e.current_answer else None,
                        route=f"/qa/{e.id}",
                    )
                )

        async def add_wishlist_rows():
            rows = await self.db.execute(
                select(WishlistItem).where(
                    WishlistItem.user_id == user_id,
                    or_(WishlistItem.title.ilike(pattern), WishlistItem.description.ilike(pattern)),
                ).limit(limit)
            )
            for w in rows.scalars().all():
                results.append(
                    SearchResultItem(
                        module="wishlist",
                        entity_type="item",
                        id=w.id,
                        title=w.title,
                        subtitle=w.category,
                        route=f"/wishlist/{w.id}",
                    )
                )

        await add_goal_rows()
        await add_task_rows()
        await add_habit_rows()
        await add_run_rows()
        await add_calendar_rows()
        await add_journal_rows()
        await add_vocab_rows()
        await add_writing_rows()
        await add_speaking_rows()
        await add_qa_rows()
        await add_wishlist_rows()

        results = results[:limit]
        return SearchResponse(query=q, total=len(results), results=results)

    async def semantic_search(self, user_id: str, query: str, limit: int = 20) -> SearchResponse:
        q = query.strip()
        if not q:
            return SearchResponse(query=q, total=0, results=[])
        ai = AiService(self.db)
        rows = await ai.repo.list_for_user(user_id)
        if not rows:
            await ai.index(user_id)
            rows = await ai.repo.list_for_user(user_id)
        sources = await ai._retrieve(user_id, q, rows)
        results = [
            SearchResultItem(
                module=s.source_type,
                entity_type=s.source_type,
                id=s.source_id,
                title=s.title,
                subtitle=s.snippet[:80] if s.snippet else None,
                route=s.route,
            )
            for s in sources[:limit]
        ]
        if not results:
            return await self.search(user_id, q, limit=limit)
        return SearchResponse(query=q, total=len(results), results=results)
