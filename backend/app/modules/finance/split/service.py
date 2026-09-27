"""Split Bills use cases.

Rules that shape this module:

1. **The code grants read; the seat grants write.** Anyone with the short code can
   read a group. Every mutating member action needs that member's seat secret.
2. **Money is integer paise**, and stored shares always sum to the bill.
3. **Ledger rows are append-only.** Adding a bill never rewrites settlements.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.core.timezone import as_utc, ist_now, utc_now
from app.modules.auth.models import User
from app.modules.finance.split.balances import equal_split
from app.modules.finance.split.codes import (
    expires_at_for,
    generate_code,
    hash_secret,
    new_seat_secret,
    url_path,
)
from app.modules.finance.split.models import (
    SplitExpense,
    SplitGroup,
    SplitHistory,
    SplitMember,
    SplitSettlement,
    SplitShare,
)
from app.modules.finance.split.repository import SplitRepository
from app.modules.finance.split.schemas import (
    MAX_EXPENSES,
    MAX_MEMBERS,
    ExpenseCreate,
    ExpenseOut,
    GroupCreate,
    GroupView,
    JoinRequest,
    MemberOut,
    MemberUpdate,
    SeatIssued,
    SettlementOut,
    ShareOut,
)
from app.modules.finance.split.upi import rupees_to_paise

_CODE_ATTEMPTS = 5


def _member_out(member: SplitMember) -> MemberOut:
    return MemberOut(
        id=member.id,
        display_name=member.display_name,
        seat_no=member.seat_no,
        is_creator=member.is_creator,
        upi_vpa=member.upi_vpa,
        joined_at=as_utc(member.joined_at),
    )


def _expense_out(expense: SplitExpense, shares: list[SplitShare]) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        title=expense.title,
        amount_paise=expense.amount_paise,
        paid_by=expense.paid_by,
        created_by=expense.created_by,
        expense_date=expense.expense_date,
        created_at=as_utc(expense.created_at),
        shares=[ShareOut(member_id=s.member_id, amount_paise=s.amount_paise) for s in shares],
    )


def _settlement_out(settlement: SplitSettlement) -> SettlementOut:
    return SettlementOut(
        id=settlement.id,
        payer_member_id=settlement.payer_member_id,
        payee_member_id=settlement.payee_member_id,
        amount_paise=settlement.amount_paise,
        status=settlement.status,
        method=settlement.method,
        paid_at=as_utc(settlement.paid_at),
        confirmed_at=as_utc(settlement.confirmed_at) if settlement.confirmed_at else None,
    )


class SplitService:
    def __init__(self, db: AsyncSession):
        self.repo = SplitRepository(db)

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------

    async def create_group(self, data: GroupCreate, user: User | None) -> SeatIssued:
        now = utc_now()
        group = SplitGroup(
            code=await self._unused_code(),
            name=data.name,
            owner_user_id=user.id if user else None,
            expires_at=expires_at_for(data.expiry, now),
            created_at=now,
        )
        await self.repo.add(group)
        secret = new_seat_secret()
        creator = SplitMember(
            group_id=group.id,
            seat_no=0,
            display_name=data.creator_name,
            user_id=user.id if user else None,
            secret_hash=hash_secret(secret),
            joined_at=now,
        )
        rows: list[object] = [creator]
        if user is not None:
            rows.append(SplitHistory(user_id=user.id, group_id=group.id))
        await self.repo.add(*rows)
        return SeatIssued(
            code=group.code,
            url_path=url_path(group.code),
            member_id=creator.id,
            seat_secret=secret,
            expires_at=as_utc(group.expires_at),
        )

    async def get_group(self, code: str, seat_secret: str | None, user: User | None) -> GroupView:
        group = await self._group(code)
        members = await self.repo.list_members(group.id)
        me = await self._optional_seat(group, seat_secret)
        expenses = await self.repo.list_expenses(group.id)
        shares_by_expense: dict[str, list[SplitShare]] = {}
        for share in await self.repo.list_shares(group.id):
            shares_by_expense.setdefault(share.expense_id, []).append(share)
        order = {m.id: m.seat_no for m in members}
        for shares in shares_by_expense.values():
            shares.sort(key=lambda s: order.get(s.member_id, 0))
        settlements = await self.repo.list_settlements(group.id)
        return GroupView(
            code=group.code,
            name=group.name,
            url_path=url_path(group.code),
            created_at=as_utc(group.created_at),
            expires_at=as_utc(group.expires_at),
            ended_at=as_utc(group.ended_at) if group.ended_at else None,
            is_open=group.is_open_at(utc_now()),
            members=[_member_out(m) for m in members],
            expenses=[_expense_out(e, shares_by_expense.get(e.id, [])) for e in expenses],
            settlements=[_settlement_out(s) for s in settlements],
            my_member_id=me.id if me else None,
            is_creator=bool(me and me.is_creator),
            in_history=await self.repo.has_history(user.id, group.id) if user else None,
        )

    # ------------------------------------------------------------------
    # Seats
    # ------------------------------------------------------------------

    async def join(self, code: str, data: JoinRequest, user: User | None) -> SeatIssued:
        group = await self._group(code)
        self._require_open(group)
        members = await self.repo.list_members(group.id)
        if len(members) >= MAX_MEMBERS:
            raise ConflictError(f"This group is full ({MAX_MEMBERS} people)")
        secret = new_seat_secret()
        member = SplitMember(
            group_id=group.id,
            seat_no=members[-1].seat_no + 1,
            display_name=data.display_name,
            user_id=user.id if user else None,
            secret_hash=hash_secret(secret),
        )
        try:
            await self.repo.add(member)
        except IntegrityError as exc:  # two joins raced for the same seat number
            raise ConflictError("Someone joined at the same moment, try again") from exc
        return SeatIssued(
            code=group.code,
            url_path=url_path(group.code),
            member_id=member.id,
            seat_secret=secret,
            expires_at=as_utc(group.expires_at),
        )

    async def update_me(self, code: str, seat_secret: str | None, data: MemberUpdate) -> MemberOut:
        group = await self._group(code)
        me = await self._require_seat(group, seat_secret)
        me.upi_vpa = data.upi_vpa
        await self.repo.add(me)
        return _member_out(me)

    # ------------------------------------------------------------------
    # Bills
    # ------------------------------------------------------------------

    async def add_expense(self, code: str, seat_secret: str | None, data: ExpenseCreate) -> ExpenseOut:
        group = await self._group(code)
        me = await self._require_seat(group, seat_secret)
        self._require_open(group)
        if await self.repo.count_expenses(group.id) >= MAX_EXPENSES:
            raise ConflictError(f"This group has reached {MAX_EXPENSES} bills")
        seat_order = {m.id: m.seat_no for m in await self.repo.list_members(group.id)}
        if any(member_id not in seat_order for member_id in data.member_ids):
            raise BadRequestError("Every person on a bill must have joined the group")
        if data.paid_by not in data.member_ids:
            raise BadRequestError("Whoever paid must be included on the bill")
        amount_paise = rupees_to_paise(data.amount_rupees)
        included = sorted(data.member_ids, key=seat_order.__getitem__)
        expense = SplitExpense(
            group_id=group.id,
            paid_by=data.paid_by,
            title=data.title,
            amount_paise=amount_paise,
            expense_date=ist_now().date(),
            created_by=me.id,
        )
        await self.repo.add(expense)
        shares = [
            SplitShare(expense_id=expense.id, member_id=member_id, amount_paise=share)
            for member_id, share in equal_split(amount_paise, included)
        ]
        await self.repo.add(*shares)
        return _expense_out(expense, shares)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_open(group: SplitGroup) -> None:
        if group.ended_at is not None:
            raise ConflictError("This link has ended")
        if not group.is_open_at(utc_now()):
            raise ConflictError("This link has expired")

    async def _unused_code(self) -> str:
        for _ in range(_CODE_ATTEMPTS):
            code = generate_code()
            if not await self.repo.code_exists(code):
                return code
        raise ServiceUnavailableError("Could not allocate a group code, try again")

    async def _group(self, code: str) -> SplitGroup:
        group = await self.repo.get_group_by_code(code)
        if group is None:
            raise NotFoundError("Group not found")
        return group

    async def _optional_seat(self, group: SplitGroup, seat_secret: str | None) -> SplitMember | None:
        if not seat_secret:
            return None
        return await self.repo.find_member_by_secret_hash(group.id, hash_secret(seat_secret))

    async def _require_seat(self, group: SplitGroup, seat_secret: str | None) -> SplitMember:
        member = await self._optional_seat(group, seat_secret)
        if member is None:
            raise ForbiddenError("Join this group to do that")
        return member
