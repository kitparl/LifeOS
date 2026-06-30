import csv
import io
import json
from typing import Any

from fastapi import HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarEvent
from app.modules.communication.models import VocabularyWord
from app.modules.goals.models import Goal
from app.modules.habits.models import Habit
from app.modules.journal.models import JournalEntry
from app.modules.qa.models import QAEntry
from app.modules.running.models import Run
from app.modules.tasks.models import Task
from app.modules.wishlist.models import WishlistItem

EXPORT_MODULES = (
    "goals",
    "tasks",
    "habits",
    "runs",
    "journal",
    "calendar",
    "qa",
    "wishlist",
    "vocabulary",
    "all",
)


class ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _rows_for_module(self, user_id: str, module: str) -> list[dict[str, Any]]:
        if module == "goals":
            result = await self.db.execute(select(Goal).where(Goal.user_id == user_id))
            return [
                {
                    "id": g.id,
                    "title": g.title,
                    "category": g.category,
                    "status": g.status,
                    "progress": g.progress,
                    "target_date": str(g.target_date) if g.target_date else None,
                }
                for g in result.scalars().all()
            ]
        if module == "tasks":
            result = await self.db.execute(select(Task).where(Task.user_id == user_id))
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "due_date": str(t.due_date) if t.due_date else None,
                }
                for t in result.scalars().all()
            ]
        if module == "habits":
            result = await self.db.execute(select(Habit).where(Habit.user_id == user_id))
            return [
                {"id": h.id, "name": h.name, "frequency": h.frequency, "is_active": h.is_active}
                for h in result.scalars().all()
            ]
        if module == "runs":
            result = await self.db.execute(select(Run).where(Run.user_id == user_id))
            return [
                {
                    "id": r.id,
                    "run_date": str(r.run_date),
                    "distance_km": r.distance_km,
                    "duration_seconds": r.duration_seconds,
                }
                for r in result.scalars().all()
            ]
        if module == "journal":
            result = await self.db.execute(select(JournalEntry).where(JournalEntry.user_id == user_id))
            return [
                {
                    "id": j.id,
                    "entry_date": str(j.entry_date),
                    "entry_type": j.entry_type,
                    "title": j.title,
                    "content": j.content,
                }
                for j in result.scalars().all()
            ]
        if module == "calendar":
            result = await self.db.execute(select(CalendarEvent).where(CalendarEvent.user_id == user_id))
            return [
                {
                    "id": e.id,
                    "title": e.title,
                    "starts_at": e.starts_at.isoformat(),
                    "category": e.category,
                }
                for e in result.scalars().all()
            ]
        if module == "qa":
            result = await self.db.execute(select(QAEntry).where(QAEntry.user_id == user_id))
            return [
                {"id": e.id, "question": e.question, "answer": e.current_answer, "tags": e.tags_json}
                for e in result.scalars().all()
            ]
        if module == "wishlist":
            result = await self.db.execute(select(WishlistItem).where(WishlistItem.user_id == user_id))
            return [
                {
                    "id": w.id,
                    "title": w.title,
                    "category": w.category,
                    "cost": w.cost,
                    "progress": w.progress,
                }
                for w in result.scalars().all()
            ]
        if module == "vocabulary":
            result = await self.db.execute(select(VocabularyWord).where(VocabularyWord.user_id == user_id))
            return [
                {"id": w.id, "word": w.word, "meaning": w.meaning, "mastery": w.mastery}
                for w in result.scalars().all()
            ]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown export module")

    async def export(self, user_id: str, module: str, fmt: str) -> Response:
        if module not in EXPORT_MODULES:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown export module")
        if fmt not in ("json", "csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format must be json or csv")
        if module == "all" and fmt == "csv":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use json format for all-modules export",
            )

        if module == "all":
            payload = {}
            for m in EXPORT_MODULES:
                if m == "all":
                    continue
                payload[m] = await self._rows_for_module(user_id, m)
            rows = None
        else:
            payload = None
            rows = await self._rows_for_module(user_id, module)

        filename = f"lifeos-{module}.{fmt}"
        if fmt == "json":
            content = json.dumps(payload if module == "all" else rows, indent=2, default=str)
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        buffer = io.StringIO()
        if not rows:
            writer = csv.writer(buffer)
            writer.writerow(["empty"])
        else:
            writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
