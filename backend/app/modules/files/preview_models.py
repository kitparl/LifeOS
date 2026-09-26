from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.timezone import utc_now


class DocumentPreview(Base):
    """Conversion/cache state for a FileRecord's preview, keyed by file_id.

    One row per file. `cache_key` mixes the file's content checksum with the
    converter version so a source re-upload (new checksum) or a LibreOffice/
    converter upgrade (new version) invalidates the cache automatically.
    """

    __tablename__ = "document_previews"

    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("file_records.id"), primary_key=True
    )
    cache_key: Mapped[str] = mapped_column(String(160), nullable=False)
    preview_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="processing")
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cache_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
