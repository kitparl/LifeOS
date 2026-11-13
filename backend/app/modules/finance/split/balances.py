"""Pure Split Bills arithmetic on integer paise. No I/O — every function here is property-tested.

Debts are simplified: each person's net balance (paid − own shares ± confirmed payments) is
settled with the fewest transfers, largest debtor paying largest creditor first. So nobody who
is owed money is ever asked to pay, and circular debts (A→B→C→A) cancel out.
"""

from collections.abc import Iterable, Mapping, Sequence
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


def simplify_debts(member_ids: Sequence[str], nets: Mapping[str, int]) -> list[Debt]:
    """Settle `nets` (which sum to zero) with at most n − 1 transfers, ordered by seat of (payer, payee).

    Greedy: the biggest debtor pays the biggest creditor; ties go to the earlier seat. Each step
    clears one side, so a pair never repeats and every debt is positive.
    """
    seat = {member_id: index for index, member_id in enumerate(member_ids)}
    owing = {m: -nets[m] for m in member_ids if nets[m] < 0}
    owed = {m: nets[m] for m in member_ids if nets[m] > 0}

    def biggest(balances: dict[str, int]) -> str:
        return max(balances, key=lambda m: (balances[m], -seat[m]))

    debts: list[Debt] = []
    while owing and owed:
        payer, payee = biggest(owing), biggest(owed)
        amount = min(owing[payer], owed[payee])
        debts.append(Debt(payer=payer, payee=payee, amount=amount))
        for balances, member_id in ((owing, payer), (owed, payee)):
            balances[member_id] -= amount
            if balances[member_id] == 0:
                del balances[member_id]
    return sorted(debts, key=lambda d: (seat[d.payer], seat[d.payee]))


def payable(debt: Debt, pending: Iterable[Payment]) -> int:
    """What is still to pay on a debt once payments marked paid (not yet confirmed) are set aside."""
    marked = sum(p.amount for p in pending if (p.payer, p.payee) == (debt.payer, debt.payee))
    return max(0, debt.amount - marked)
