from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, new_id
from app.core.timezone import utc_now


class KnowledgeSubject(Base):
    """Top-level knowledge area (e.g. "System Design", "Spanish")."""

    __tablename__ = "knowledge_subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(16), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    chapters: Mapped[list["KnowledgeChapter"]] = relationship(
        "KnowledgeChapter",
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="KnowledgeChapter.order_index",
    )


class KnowledgeChapter(Base):
    """A chapter within a subject. The hierarchy is intentionally flexible:
    a subject may have many chapters, and each chapter many sections."""

    __tablename__ = "knowledge_chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    subject: Mapped["KnowledgeSubject"] = relationship("KnowledgeSubject", back_populates="chapters")
    sections: Mapped[list["KnowledgeSection"]] = relationship(
        "KnowledgeSection",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="KnowledgeSection.order_index",
    )


class KnowledgeSection(Base):
    """A section holding Markdown content (supports images, code, tables,
    lists, checklists, links — anything the shared Markdown renderer allows)."""

    __tablename__ = "knowledge_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_chapters.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    chapter: Mapped["KnowledgeChapter"] = relationship("KnowledgeChapter", back_populates="sections")
