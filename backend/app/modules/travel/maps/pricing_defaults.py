"""Seed rows for `map_pricing_configurations` — data only, copied once per user and then user-edited.

Values follow Google Maps Platform's published "Essentials" list prices at the time of writing
(USD per 1,000 requests, with the monthly free usage per SKU). They are defaults to verify against
https://mapsplatform.google.com/pricing/ — the usage screen asks for a review every 90 days.
No code path reads these constants except `UsageService.ensure_defaults`.
"""

from decimal import Decimal

from app.modules.travel.maps.types import Sku

DEFAULT_PRICING: tuple[tuple[Sku, str, Decimal, int], ...] = (
    (Sku.GEOCODING, "Geocoding", Decimal("5.00"), 10_000),
    (Sku.PLACES_AUTOCOMPLETE, "Place search (autocomplete)", Decimal("2.83"), 10_000),
    (Sku.PLACE_DETAILS, "Place details", Decimal("5.00"), 10_000),
    (Sku.ROUTES, "Routes", Decimal("5.00"), 10_000),
    (Sku.ELEVATION, "Elevation", Decimal("5.00"), 10_000),
)

# Units of currency per 1 USD, used to show estimates in the user's currency preference.
DEFAULT_FX_RATES: dict[str, float] = {"INR": 83.0}
