from pydantic import BaseModel, Field


COACH_TYPES = ("running", "career", "finance", "learning", "communication", "habits")


class CoachChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class CoachChatResponse(BaseModel):
    coach_type: str
    reply: str
    context_summary: str
