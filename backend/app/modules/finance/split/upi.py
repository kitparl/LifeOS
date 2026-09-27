"""Rupee/paise conversion and the UPI payment intent. LifeOS never moves money or stores the intent."""

from decimal import Decimal
from urllib.parse import quote


def rupees_to_paise(rupees: Decimal) -> int:
    """`round(rupees * 100)`; exact for the ≤ 2-decimal amounts the API accepts."""
    return int((rupees * 100).to_integral_value())


def paise_to_rupees(paise: int) -> str:
    """`30000` -> `"300.00"` (the UPI `am` format)."""
    return f"{paise // 100}.{paise % 100:02d}"


def build_upi_uri(payee_vpa: str | None, payee_name: str, amount_paise: int, note: str) -> str:
    """`upi://pay?pa=…&pn=…&am=…&cu=INR&tn=…` for one payment. Raises when the payee has no VPA."""
    if not payee_vpa:
        raise ValueError("The payee has no UPI id")
    params = (
        ("pa", quote(payee_vpa, safe="@")),
        ("pn", quote(payee_name, safe="")),
        ("am", paise_to_rupees(amount_paise)),
        ("cu", "INR"),
        ("tn", quote(note, safe="")),
    )
    return "upi://pay?" + "&".join(f"{key}={value}" for key, value in params)
