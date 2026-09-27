"""Rupee/paise conversion for Split Bills."""

from decimal import Decimal


def rupees_to_paise(rupees: Decimal) -> int:
    """`round(rupees * 100)`; exact for the ≤ 2-decimal amounts the API accepts."""
    return int((rupees * 100).to_integral_value())


def paise_to_rupees(paise: int) -> str:
    """`30000` -> `"300.00"` (the UPI `am` format)."""
    return f"{paise // 100}.{paise % 100:02d}"
