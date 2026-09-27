from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.modules.finance.split.codes import Expiry

GroupName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


# --------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------

class GroupCreate(BaseModel):
    name: GroupName
    creator_name: DisplayName
    expiry: Expiry


# --------------------------------------------------------------------------
# Responses — never carry secret hashes, user ids or emails
# --------------------------------------------------------------------------

class SeatIssued(BaseModel):
    """One-time response carrying the raw seat secret (create and join only)."""

    code: str
    url_path: str
    member_id: str
    seat_secret: str
    expires_at: datetime


class MemberOut(BaseModel):
    id: str
    display_name: str
    seat_no: int
    is_creator: bool
    upi_vpa: str | None
    joined_at: datetime


class ShareOut(BaseModel):
    member_id: str
    amount_paise: int


class ExpenseOut(BaseModel):
    id: str
    title: str
    amount_paise: int
    paid_by: str
    created_by: str
    expense_date: date
    created_at: datetime
    shares: list[ShareOut]


class SettlementOut(BaseModel):
    id: str
    payer_member_id: str
    payee_member_id: str
    amount_paise: int
    status: str
    method: str
    paid_at: datetime
    confirmed_at: datetime | None


class GroupView(BaseModel):
    code: str
    name: str
    url_path: str
    created_at: datetime
    expires_at: datetime
    ended_at: datetime | None
    is_open: bool
    members: list[MemberOut]
    expenses: list[ExpenseOut]
    settlements: list[SettlementOut]
    # Viewer context: resolved from the optional seat secret / Bearer token.
    my_member_id: str | None
    is_creator: bool
    in_history: bool | None
