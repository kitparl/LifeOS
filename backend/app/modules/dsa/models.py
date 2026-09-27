"""DSA practice tables.

The catalog (patterns, problems, test cases) is global and admin-edited. Submissions and progress
are per user; every user-facing query on them filters by `user_id` (see repository.py).
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now


class DsaPattern(Base):
    __tablename__ = "dsa_patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DsaProblem(Base):
    __tablename__ = "dsa_problems"
    __table_args__ = (Index("ix_dsa_problems_pattern_order", "pattern_id", "display_order"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pattern_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dsa_patterns.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_variant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="draft")
    statement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    constraints: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # SignatureSpec as JSON; null while the problem is a draft.
    signature: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    compare_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="exact")
    checker: Mapped[str | None] = mapped_column(String(60), nullable=True)
    time_limit_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=256)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    # sha256 of the seed payload last applied; lets the seeder skip unchanged problems.
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Set by any admin-UI save; the seeder leaves such problems alone unless --force.
    edited_in_ui: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DsaTestCase(Base):
    __tablename__ = "dsa_test_cases"
    __table_args__ = (
        UniqueConstraint("problem_id", "position", name="uq_dsa_test_problem_position"),
        Index("ix_dsa_test_problem_sample", "problem_id", "is_sample"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dsa_problems.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    # Function problems: list of positional args. Class problems: {"ops": [...], "args": [...]}.
    input: Mapped[list | dict] = mapped_column(JSON, nullable=False)
    expected: Mapped[object] = mapped_column(JSON, nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="manual")
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)


class DsaSubmission(Base):
    __tablename__ = "dsa_submissions"
    __table_args__ = (Index("ix_dsa_sub_user_problem_created", "user_id", "problem_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dsa_problems.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(10), index=True, nullable=False, default="pending")
    verdict: Mapped[str | None] = mapped_column(String(24), nullable=True)
    passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Compiler output or runtime error text (truncated); stderr only when safe to show (see service).
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DsaUserProgress(Base):
    """One row per (user, problem) once attempted; no row means not started."""

    __tablename__ = "dsa_user_progress"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_dsa_progress_user_problem"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dsa_problems.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    best_submission_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dsa_submissions.id", ondelete="SET NULL"), nullable=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DsaNote(Base):
    """A user's private markdown note on exactly one pattern or one problem."""

    __tablename__ = "dsa_notes"
    __table_args__ = (
        UniqueConstraint("user_id", "pattern_id", name="uq_dsa_note_user_pattern"),
        UniqueConstraint("user_id", "problem_id", name="uq_dsa_note_user_problem"),
        CheckConstraint("(pattern_id IS NULL) <> (problem_id IS NULL)", name="ck_dsa_note_one_target"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    pattern_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dsa_patterns.id", ondelete="CASCADE"), nullable=True
    )
    problem_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dsa_problems.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
