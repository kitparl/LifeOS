/**
 * "Open in Google Maps" / "Get directions" via Google's public Maps URLs (spec §25).
 * Plain links: no API key, no usage, nothing synced to the user's Google account.
 */

export interface LatLngLike {
  lat: number;
  lng: number;
}

const MAX_DIRECTION_WAYPOINTS = 9; // Maps URLs accept up to 9 intermediate waypoints

function coord(p: LatLngLike): string {
  return `${p.lat.toFixed(6)},${p.lng.toFixed(6)}`;
}

export function openInGoogleMapsUrl(place: LatLngLike & { external_place_id?: string | null }): string {
  const params = new URLSearchParams({ api: '1', query: coord(place) });
  if (place.external_place_id) params.set('query_place_id', place.external_place_id);
  return `https://www.google.com/maps/search/?${params.toString()}`;
}

/** Directions to the last stop via the ones in between; the origin is the user's current location in Google Maps. */
export function directionsUrl(stops: readonly LatLngLike[], mode: 'driving' | 'walking' | 'cycling' | 'transit' = 'driving'): string | null {
  if (!stops.length) return null;
  const destination = stops[stops.length - 1];
  const via = stops.slice(0, -1).slice(-MAX_DIRECTION_WAYPOINTS);
  const params = new URLSearchParams({
    api: '1',
    destination: coord(destination),
    travelmode: mode === 'cycling' ? 'bicycling' : mode,
  });
  if (via.length) params.set('waypoints', via.map(coord).join('|'));
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}
