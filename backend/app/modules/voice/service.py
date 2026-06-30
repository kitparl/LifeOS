from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.voice.repository import VoiceRepository
from app.modules.voice.schemas import (
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceNoteCreate,
    VoiceNoteResponse,
)

ROUTE_MAP = {
    "dashboard": "/dashboard",
    "goals": "/goals",
    "tasks": "/tasks",
    "habits": "/habits",
    "running": "/running",
    "calendar": "/calendar",
    "journal": "/journal",
    "mood": "/mood",
    "finance": "/finance",
    "learning": "/learning",
    "career": "/career",
    "analytics": "/analytics",
    "timeline": "/timeline",
    "reports": "/reports",
    "search": "/search",
    "memory": "/memory",
    "coaches": "/coaches",
    "ocr": "/ocr",
    "voice": "/voice",
    "integrations": "/integrations",
    "automations": "/automations",
    "predictions": "/predictions",
    "life-timeline": "/life-timeline",
}


class VoiceService:
    def __init__(self, db: AsyncSession):
        self.repo = VoiceRepository(db)

    async def list_notes(self, user_id: str) -> list[VoiceNoteResponse]:
        notes = await self.repo.list_notes(user_id)
        return [VoiceNoteResponse.model_validate(n) for n in notes]

    async def create_note(self, user_id: str, data: VoiceNoteCreate) -> VoiceNoteResponse:
        note = await self.repo.create(user_id, data)
        return VoiceNoteResponse.model_validate(note)

    async def interpret_command(self, user_id: str, data: VoiceCommandRequest) -> VoiceCommandResponse:
        text = data.transcript.strip().lower()
        intent = "unknown"
        route: str | None = None
        message = "Command not recognized. Try: go to tasks, log run, open finance, search goals."

        if text.startswith("go to ") or text.startswith("open "):
            target = text.split(" ", 2)[-1].strip()
            for key, path in ROUTE_MAP.items():
                if key in target or target in key:
                    intent = "navigate"
                    route = path
                    message = f"Navigate to {path}"
                    break
        elif "log run" in text or "new run" in text:
            intent = "navigate"
            route = "/running/new"
            message = "Open run form"
        elif text.startswith("search "):
            query = data.transcript[7:].strip()
            intent = "search"
            route = f"/search?q={query}"
            message = f"Search for: {query}"
        elif "new task" in text:
            intent = "navigate"
            route = "/tasks/new"
            message = "Open new task form"
        elif "new journal" in text:
            intent = "navigate"
            route = "/journal/new"
            message = "Open new journal entry"

        result = VoiceCommandResponse(intent=intent, route=route, message=message, transcript=data.transcript)
        await self.repo.create(
            user_id,
            VoiceNoteCreate(transcript=data.transcript, note_type="command", title="Voice command"),
            command_result=message,
        )
        return result

    async def delete_note(self, user_id: str, note_id: str) -> None:
        note = await self.repo.delete(user_id, note_id)
        if not note:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Voice note not found")
