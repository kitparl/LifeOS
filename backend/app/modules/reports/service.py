from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.service import AiService
from app.modules.ai.use_cases import USE_CASE_REPORTS


class ReviewResponse(BaseModel):
    review_type: str
    generated_at: datetime
    content: str


class ReportsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = AiService(db)

    async def generate_review(self, user_id: str, review_type: str) -> ReviewResponse:
        prompts = {
            "daily": "Give me a concise daily review: what should I focus on today based on my tasks?",
            "weekly": "Give me a weekly review: wins, gaps, and priorities for next week.",
            "monthly": "Give me a monthly review: progress across tasks, habits, running, and finance.",
        }
        prompt = prompts.get(review_type, prompts["weekly"])
        chat = await self.ai.chat(user_id, prompt, use_case=USE_CASE_REPORTS)
        return ReviewResponse(
            review_type=review_type,
            generated_at=datetime.now(timezone.utc),
            content=chat.reply,
        )
