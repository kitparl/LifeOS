from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ocr.models import OcrDocument
from app.modules.ocr.schemas import OcrDocumentCreate


class OcrRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_documents(self, user_id: str) -> list[OcrDocument]:
        result = await self.db.execute(
            select(OcrDocument).where(OcrDocument.user_id == user_id).order_by(OcrDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, doc_id: str) -> OcrDocument | None:
        result = await self.db.execute(
            select(OcrDocument).where(OcrDocument.id == doc_id, OcrDocument.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: OcrDocumentCreate, extracted_text: str | None, status: str) -> OcrDocument:
        doc = OcrDocument(
            user_id=user_id,
            filename=data.filename,
            doc_type=data.doc_type,
            file_id=data.file_id,
            extracted_text=extracted_text,
            status=status,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def delete(self, doc: OcrDocument) -> None:
        await self.db.delete(doc)
