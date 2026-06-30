from datetime import datetime

from pydantic import BaseModel, Field


class VoiceNoteCreate(BaseModel):
    transcript: str = Field(min_length=1)
    title: str | None = Field(default=None, max_length=200)
    note_type: str = "note"
    audio_file_id: str | None = None


class VoiceCommandRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=500)


class VoiceCommandResponse(BaseModel):
    intent: str
    route: str | None = None
    message: str
    transcript: str


class VoiceNoteResponse(BaseModel):
    id: str
    title: str | None
    transcript: str
    note_type: str
    audio_file_id: str | None
    command_result: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
