"""Map lookups (reverse geocode, search, place details) with graceful fallback.

Every lookup goes through `MapsGateway`. When Google is not configured, blocked by cost protection
or failing, the caller gets `fallback_reason` instead of an error so the UI can continue with
coordinates only (requirements D-01) — saving a place never depends on Google.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.modules.travel.maps.errors import MapsError
from app.modules.travel.maps.gateway import MapsGateway
from app.modules.travel.maps.types import Feature, GeoResult, Sku
from app.modules.travel.schemas.places import GeoLookupOut, GeoOut, SuggestionOut, SuggestionsOut
from app.modules.travel.schemas.usage import MapsStatus
from app.modules.travel.services.usage_service import UsageService

MIN_QUERY_LENGTH = 3


def _geo_out(result: GeoResult) -> GeoOut:
    return GeoOut(
        name=result.name,
        address=result.address,
        country=result.country,
        region=result.region,
        city=result.city,
        lat=result.lat,
        lng=result.lng,
        external_place_id=result.external_place_id,
    )


class LookupService:
    def __init__(self, db: AsyncSession):
        self.gateway = MapsGateway(db)
        self.usage = UsageService(db)

    async def reverse_geocode(self, user_id: str, lat: float, lng: float) -> GeoLookupOut:
        try:
            result = await self.gateway.call(
                user_id, Sku.GEOCODING, Feature.MAP_TAP, lambda p: p.reverse_geocode(lat, lng)
            )
        except MapsError as exc:
            return GeoLookupOut(result=None, fallback_reason=exc.code)
        if result is None:
            return GeoLookupOut(result=None, fallback_reason="no_result")
        return GeoLookupOut(result=_geo_out(result))

    async def autocomplete(
        self, user_id: str, query: str, session_token: str, bias: tuple[float, float] | None
    ) -> SuggestionsOut:
        query = query.strip()
        if len(query) < MIN_QUERY_LENGTH:
            raise BadRequestError(f"Type at least {MIN_QUERY_LENGTH} characters")
        try:
            items = await self.gateway.call(
                user_id,
                Sku.PLACES_AUTOCOMPLETE,
                Feature.SEARCH,
                lambda p: p.autocomplete(query, session_token, bias),
            )
        except MapsError as exc:
            return SuggestionsOut(suggestions=[], fallback_reason=exc.code)
        return SuggestionsOut(
            suggestions=[
                SuggestionOut(external_place_id=s.external_place_id, primary=s.primary, secondary=s.secondary)
                for s in items
            ]
        )

    async def place_details(self, user_id: str, external_place_id: str, session_token: str | None) -> GeoLookupOut:
        try:
            result = await self.gateway.call(
                user_id,
                Sku.PLACE_DETAILS,
                Feature.SEARCH_SELECT,
                lambda p: p.place_details(external_place_id, session_token),
            )
        except MapsError as exc:
            return GeoLookupOut(result=None, fallback_reason=exc.code)
        return GeoLookupOut(result=_geo_out(result))

    async def status(self, user_id: str) -> MapsStatus:
        return await self.usage.maps_status(user_id, configured=await self.gateway.is_configured(user_id))
