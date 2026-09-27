"""Pure Split Bills arithmetic on integer paise. No I/O — every function here is property-tested."""

from collections.abc import Sequence


def equal_split(amount_paise: int, member_ids: Sequence[str]) -> list[tuple[str, int]]:
    """Split `amount_paise` equally across `member_ids` (given in stable join order).

    The first `amount % n` members get one extra paise, so the shares always sum to the amount.
    """
    if not member_ids:
        raise ValueError("equal_split needs at least one member")
    base, remainder = divmod(amount_paise, len(member_ids))
    return [(member_id, base + (1 if index < remainder else 0)) for index, member_id in enumerate(member_ids)]
