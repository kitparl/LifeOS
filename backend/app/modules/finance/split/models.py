"""Split Bills tables.

A group lives on the server and is reached by its short `code`. People take a
seat by joining; each seat is authorised by a random secret of which only the
hash is stored. Amounts are integer paise.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import as_utc, utc_now


class SplitGroup(Base):
    __tablename__ = "split_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    owner_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    def is_open_at(self, now: datetime) -> bool:
        """The link accepts joins and bills until the creator ends it or it expires."""
        return self.ended_at is None and now < as_utc(self.expires_at)


class SplitMember(Base):
    """A seat in a group. `seat_no` is the stable join order (0 = creator)."""

    __tablename__ = "split_members"
    __table_args__ = (UniqueConstraint("group_id", "seat_no", name="uq_split_member_seat"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_groups.id"), index=True, nullable=False)
    seat_no: Mapped[int] = mapped_column(Integer, nullable=False)
    display_name: Mapped[str] = mapped_column(String(40), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    secret_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    upi_vpa: Mapped[str | None] = mapped_column(String(129), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @property
    def is_creator(self) -> bool:
        return self.seat_no == 0


class SplitExpense(Base):
    __tablename__ = "split_expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_groups.id"), index=True, nullable=False)
    paid_by: Mapped[str] = mapped_column(String(36), ForeignKey("split_members.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("split_members.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SplitShare(Base):
    __tablename__ = "split_shares"
    __table_args__ = (UniqueConstraint("expense_id", "member_id", name="uq_split_share_member"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    expense_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_expenses.id"), index=True, nullable=False)
    member_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_members.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)


class SplitSettlement(Base):
    """A payment between two seats. Only `confirmed` rows move balances."""

    __tablename__ = "split_settlements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_groups.id"), index=True, nullable=False)
    payer_member_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_members.id"), nullable=False)
    payee_member_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_members.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    upi_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SplitHistory(Base):
    """A signed-in user's saved group; outlives the link."""

    __tablename__ = "split_history"
    __table_args__ = (UniqueConstraint("user_id", "group_id", name="uq_split_history_user_group"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("split_groups.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
