from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.ocr.schemas import OcrDocumentCreate, OcrDocumentResponse
from app.modules.ocr.service import OcrService
from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.get("/documents", response_model=list[OcrDocumentResponse])
async def list_ocr_documents(
    response: Response,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await OcrService(db).list_documents(user.id, limit=limit, offset=offset)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/documents", response_model=OcrDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_ocr_from_text(
    data: OcrDocumentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OcrService(db).process_text(user.id, data)


@router.post("/documents/upload", response_model=OcrDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_ocr_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default="document"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OcrService(db).process_upload(user.id, file, doc_type)


@router.get("/documents/{doc_id}", response_model=OcrDocumentResponse)
async def get_ocr_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OcrService(db).get_document(user.id, doc_id)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ocr_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await OcrService(db).delete_document(user.id, doc_id)
