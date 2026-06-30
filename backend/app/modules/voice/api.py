from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.voice.schemas import (
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceNoteCreate,
    VoiceNoteResponse,
)
from app.modules.voice.service import VoiceService

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/notes", response_model=list[VoiceNoteResponse])
async def list_voice_notes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VoiceService(db).list_notes(user.id)


@router.post("/notes", response_model=VoiceNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_note(
    data: VoiceNoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VoiceService(db).create_note(user.id, data)


@router.post("/command", response_model=VoiceCommandResponse)
async def voice_command(
    data: VoiceCommandRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VoiceService(db).interpret_command(user.id, data)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_note(
    note_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await VoiceService(db).delete_note(user.id, note_id)
