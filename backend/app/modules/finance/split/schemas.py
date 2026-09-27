import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.modules.finance.split.codes import Expiry

GroupName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
BillTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
MemberId = Annotated[str, StringConstraints(min_length=1, max_length=36)]
# Rupees with at most 2 decimals; stored as integer paise.
RupeeAmount = Annotated[Decimal, Field(gt=0, le=10_000_000, decimal_places=2)]

MAX_MEMBERS = 50
MAX_EXPENSES = 100

# `name@bank`: a UPI virtual payment address.
UPI_VPA_PATTERN = r"^[a-z0-9._-]{2,64}@[a-z0-9.-]{2,64}$"


# --------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------

class GroupCreate(BaseModel):
    name: GroupName
    creator_name: DisplayName
    expiry: Expiry


class JoinRequest(BaseModel):
    display_name: DisplayName


class ExpenseCreate(BaseModel):
    title: BillTitle
    amount_rupees: RupeeAmount
    paid_by: MemberId
    member_ids: list[MemberId] = Field(min_length=1, max_length=MAX_MEMBERS)

    @field_validator("member_ids")
    @classmethod
    def _unique(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("member_ids must be unique")
        return value


SettlementMethod = Literal["upi", "cash"]


class SettlementCreate(BaseModel):
    payee_member_id: MemberId
    amount_rupees: RupeeAmount
    method: SettlementMethod


class UpiLinkRequest(BaseModel):
    payee_member_id: MemberId
    amount_rupees: RupeeAmount


class MemberUpdate(BaseModel):
    """`upi_vpa` null or blank clears it."""

    upi_vpa: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=129)] | None = None

    @field_validator("upi_vpa")
    @classmethod
    def _vpa_shape(cls, value: str | None) -> str | None:
        if not value:
            return None
        if not re.fullmatch(UPI_VPA_PATTERN, value):
            raise ValueError("Enter a UPI id like name@bank")
        return value


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


class MemberBalanceOut(BaseModel):
    member_id: str
    display_name: str
    net_paise: int


class DebtOut(BaseModel):
    """One outstanding payer -> payee debt. `amount_*` is the price still to pay now."""

    payer_member_id: str
    payer_name: str
    payee_member_id: str
    payee_name: str
    outstanding_paise: int  # confirmed-only remainder
    pending_paise: int  # marked paid, awaiting the payee's confirmation
    amount_paise: int
    amount_rupees: str
    upi_uri: str | None  # null when the payee has no UPI id or nothing is left to pay


class BalancesOut(BaseModel):
    nets: list[MemberBalanceOut]
    debts: list[DebtOut]


class UpiLinkOut(BaseModel):
    upi_uri: str


class HistoryItemOut(BaseModel):
    code: str
    name: str
    url_path: str
    expires_at: datetime
    ended_at: datetime | None
    is_open: bool
    my_net_paise: int | None  # null when this account has no seat linked in the group
    kept_at: datetime
