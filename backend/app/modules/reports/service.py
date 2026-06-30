from datetime import UTC, datetime, timedelta

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.service import AiService
from app.modules.analytics.service import AnalyticsService


class ReportSection(BaseModel):
    title: str
    body: str


class ReportResponse(BaseModel):
    period: str
    generated_at: datetime
    sections: list[ReportSection]
    ai_summary: str | None = None


class ReviewResponse(BaseModel):
    review_type: str
    generated_at: datetime
    content: str


class ReportsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics = AnalyticsService(db)
        self.ai = AiService(db)

    async def generate_report(self, user_id: str, period: str) -> ReportResponse:
        summary = await self.analytics.summary(user_id)
        charts = await self.analytics.charts(user_id)
        sections = [
            ReportSection(
                title="Overview",
                body=(
                    f"Tasks completed: {summary.tasks_completed}. "
                    f"Habits (30d): {summary.habits_logged_30d}. Runs (30d): {summary.runs_30d}. "
                    f"Finance net: {summary.finance_net:.2f}."
                ),
            ),
            ReportSection(
                title="Learning",
                body=f"In progress: {summary.learning_in_progress} items.",
            ),
            ReportSection(
                title="Charts",
                body=(
                    f"Task statuses: {', '.join(f'{p.label}={p.value}' for p in charts.tasks_by_status)}. "
                    f"Top expenses: {', '.join(f'{p.label}={p.value}' for p in charts.expenses_by_category[:5])}."
                ),
            ),
        ]
        ai_summary = None
        prompt = f"Write a brief {period} life progress summary based on: {sections[0].body}"
        try:
            chat = await self.ai.chat(user_id, prompt)
            ai_summary = chat.reply
        except Exception:
            ai_summary = None
        return ReportResponse(
            period=period,
            generated_at=datetime.now(UTC),
            sections=sections,
            ai_summary=ai_summary,
        )

    async def generate_review(self, user_id: str, review_type: str) -> ReviewResponse:
        prompts = {
            "daily": "Give me a concise daily review: what should I focus on today based on my goals and tasks?",
            "weekly": "Give me a weekly review: wins, gaps, and priorities for next week.",
            "monthly": "Give me a monthly review: progress across goals, habits, running, learning, and finance.",
        }
        prompt = prompts.get(review_type, prompts["weekly"])
        chat = await self.ai.chat(user_id, prompt)
        return ReviewResponse(
            review_type=review_type,
            generated_at=datetime.now(UTC),
            content=chat.reply,
        )
