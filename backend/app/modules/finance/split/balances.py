"""Pure Split Bills arithmetic on integer paise. No I/O — every function here is property-tested.

Debts are pairwise with no simplification: on each bill every included non-payer owes the
payer their share; each pair is netted in both directions, minus confirmed payments between them.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Bill:
    paid_by: str
    shares: Sequence[tuple[str, int]]  # (member_id, paise)


@dataclass(frozen=True)
class Payment:
    payer: str
    payee: str
    amount: int


@dataclass(frozen=True)
class Debt:
    payer: str
    payee: str
    amount: int


def equal_split(amount_paise: int, member_ids: Sequence[str]) -> list[tuple[str, int]]:
    """Split `amount_paise` equally across `member_ids` (given in stable join order).

    The first `amount % n` members get one extra paise, so the shares always sum to the amount.
    """
    if not member_ids:
        raise ValueError("equal_split needs at least one member")
    base, remainder = divmod(amount_paise, len(member_ids))
    return [(member_id, base + (1 if index < remainder else 0)) for index, member_id in enumerate(member_ids)]


def member_nets(member_ids: Iterable[str], bills: Iterable[Bill], confirmed: Iterable[Payment]) -> dict[str, int]:
    """net = paid − own shares − confirmed received + confirmed sent. Positive: the group owes them."""
    nets = dict.fromkeys(member_ids, 0)
    for bill in bills:
        for member_id, share in bill.shares:
            nets[bill.paid_by] += share
            nets[member_id] -= share
    for payment in confirmed:
        nets[payment.payee] -= payment.amount
        nets[payment.payer] += payment.amount
    return nets


def pairwise_debts(member_ids: Sequence[str], bills: Iterable[Bill], confirmed: Iterable[Payment]) -> list[Debt]:
    """One debt per pair with a positive remainder, ordered by seat order of (payer, payee)."""
    owed: defaultdict[tuple[str, str], int] = defaultdict(int)
    for bill in bills:
        for member_id, share in bill.shares:
            if member_id != bill.paid_by:
                owed[(member_id, bill.paid_by)] += share
    for payment in confirmed:
        owed[(payment.payer, payment.payee)] -= payment.amount

    debts: list[Debt] = []
    for i, a in enumerate(member_ids):
        for b in member_ids[i + 1:]:
            balance = owed[(a, b)] - owed[(b, a)]
            if balance > 0:
                debts.append(Debt(payer=a, payee=b, amount=balance))
            elif balance < 0:
                debts.append(Debt(payer=b, payee=a, amount=-balance))
    return debts


def payable(debt: Debt, pending: Iterable[Payment]) -> int:
    """What is still to pay on a debt once payments marked paid (not yet confirmed) are set aside."""
    marked = sum(p.amount for p in pending if (p.payer, p.payee) == (debt.payer, debt.payee))
    return max(0, debt.amount - marked)
