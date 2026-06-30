from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.service import FileService
from app.modules.ocr.repository import OcrRepository
from app.modules.ocr.schemas import OcrDocumentCreate, OcrDocumentResponse


class OcrService:
    def __init__(self, db: AsyncSession):
        self.repo = OcrRepository(db)
        self.files = FileService(db)

    async def list_documents(self, user_id: str) -> list[OcrDocumentResponse]:
        docs = await self.repo.list_documents(user_id)
        return [OcrDocumentResponse.model_validate(d) for d in docs]

    async def get_document(self, user_id: str, doc_id: str) -> OcrDocumentResponse:
        doc = await self.repo.get_by_id(user_id, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "OCR document not found")
        return OcrDocumentResponse.model_validate(doc)

    async def process_text(self, user_id: str, data: OcrDocumentCreate) -> OcrDocumentResponse:
        text = data.text or ""
        status_val = "processed" if text.strip() else "failed"
        if not text.strip():
            text = "No text provided. Upload a text file or paste content for extraction."
        doc = await self.repo.create(user_id, data, text, status_val)
        return OcrDocumentResponse.model_validate(doc)

    async def process_upload(
        self, user_id: str, file: UploadFile, doc_type: str
    ) -> OcrDocumentResponse:
        content = await file.read()
        filename = file.filename or "upload"
        content_type = file.content_type or "application/octet-stream"

        uploaded = await self.files.upload(user_id, filename, content, content_type, "ocr", None)
        extracted, status_val = self._extract_text(filename, content_type, content)
        data = OcrDocumentCreate(filename=filename, doc_type=doc_type, file_id=uploaded.id)
        doc = await self.repo.create(user_id, data, extracted, status_val)
        return OcrDocumentResponse.model_validate(doc)

    def _extract_text(self, filename: str, content_type: str, content: bytes) -> tuple[str, str]:
        if content_type.startswith("text/") or filename.lower().endswith((".txt", ".md", ".csv")):
            try:
                return content.decode("utf-8", errors="replace"), "processed"
            except Exception:
                pass
        if filename.lower().endswith(".pdf"):
            return (
                "[PDF OCR stub] Install Tesseract or a PDF parser for full extraction. "
                f"Stored file: {filename} ({len(content)} bytes).",
                "processed",
            )
        if content_type.startswith("image/"):
            return (
                "[Image OCR stub] Install Tesseract (pytesseract) for image text extraction. "
                f"Stored image: {filename}.",
                "processed",
            )
        return (
            f"[Binary document] Stored {filename}. OCR not available for this format in dev mode.",
            "processed",
        )

    async def delete_document(self, user_id: str, doc_id: str) -> None:
        doc = await self.repo.get_by_id(user_id, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "OCR document not found")
        await self.repo.delete(doc)
