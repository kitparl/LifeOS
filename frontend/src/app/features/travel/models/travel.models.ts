/** DTOs mirroring `backend/app/modules/travel/schemas/*` — one shape per backend schema. */

export type PlaceStatus = 'wishlist' | 'planned' | 'visited' | 'favourite';
export type PlaceCategory =
  | 'trek'
  | 'mountain'
  | 'city'
  | 'beach'
  | 'nature'
  | 'photography'
  | 'camping'
  | 'road_trip'
  | 'adventure'
  | 'other';

export const PLACE_CATEGORIES: readonly { id: PlaceCategory; label: string }[] = [
  { id: 'trek', label: 'Treks' },
  { id: 'mountain', label: 'Mountains' },
  { id: 'city', label: 'Cities' },
  { id: 'beach', label: 'Beaches' },
  { id: 'nature', label: 'Nature' },
  { id: 'photography', label: 'Photography' },
  { id: 'camping', label: 'Camping' },
  { id: 'road_trip', label: 'Road Trips' },
  { id: 'adventure', label: 'Adventure' },
  { id: 'other', label: 'Other' },
];

export const PLACE_STATUS_LABELS: Record<PlaceStatus, string> = {
  wishlist: 'Wishlist',
  planned: 'Planned',
  visited: 'Visited',
  favourite: 'Favourite',
};

export interface Place {
  id: string;
  name: string;
  description: string | null;
  lat: number;
  lng: number;
  address: string | null;
  country: string | null;
  region: string | null;
  city: string | null;
  external_place_id: string | null;
  external_source: string | null;
  category: PlaceCategory;
  status: PlaceStatus;
  notes: string | null;
  desired_period: string | null;
  estimated_days: number | null;
  links: string[];
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface PlaceCreate {
  name: string;
  lat: number;
  lng: number;
  address?: string | null;
  country?: string | null;
  region?: string | null;
  city?: string | null;
  external_place_id?: string | null;
  category?: PlaceCategory;
  status?: PlaceStatus;
  notes?: string | null;
  description?: string | null;
  desired_period?: string | null;
  estimated_days?: number | null;
  links?: string[];
  tags?: string[];
}

export type PlaceUpdate = Partial<Omit<PlaceCreate, 'external_place_id' | 'tags'>>;

export type MarkerKind = 'place' | 'trip' | 'adventure' | 'photo';

export interface Marker {
  id: string;
  kind: MarkerKind;
  lat: number;
  lng: number;
  label: string;
  status: string | null;
  trip_id: string | null;
}

export interface GeoResult {
  name: string;
  address: string | null;
  country: string | null;
  region: string | null;
  city: string | null;
  lat: number;
  lng: number;
  external_place_id: string | null;
}

/** `result` is null when the lookup fell back; `fallback_reason` says why (no key, cost protection, error). */
export interface GeoLookup {
  result: GeoResult | null;
  fallback_reason: string | null;
}

export interface Suggestion {
  external_place_id: string;
  primary: string;
  secondary: string | null;
}

export interface Suggestions {
  suggestions: Suggestion[];
  fallback_reason: string | null;
}

export type UsageLevel = 'ok' | 'info' | 'warning' | 'high' | 'critical' | 'limit';

export interface MapsStatus {
  configured: boolean;
  level: UsageLevel;
  non_essential_blocked: boolean;
}

export interface PlaceHistory {
  place: Place;
  trips: { id: string; name: string; status: string; start_date: string | null }[];
  photo_count: number;
  recent_photo_ids: string[];
  journal_count: number;
  route_ids: string[];
}

/** Human text for a lookup fallback reason (see backend `MapsError.code`). */
export function fallbackMessage(reason: string | null): string | null {
  switch (reason) {
    case null:
      return null;
    case 'missing_credential':
      return 'Google lookup is off (no Google Maps key). Coordinates are saved; type a name.';
    case 'cost_protection':
      return 'Maps cost protection is active, so Google lookups are paused. Coordinates are saved; type a name.';
    case 'no_result':
      return 'No named place here. Type a name.';
    default:
      return 'Google lookup is unavailable right now. Coordinates are saved; type a name.';
  }
}

/** Marker colour per place status (CSS tokens, resolved by the map component). */
export const PLACE_STATUS_COLORS: Record<PlaceStatus, string> = {
  wishlist: '--favorite',
  planned: '--info',
  visited: '--success',
  favourite: '--warning',
};

export type MapLayer = 'wishlist' | 'planned' | 'visited' | 'favourite' | 'trips' | 'adventures' | 'photos';

export const MAP_LAYERS: readonly { id: MapLayer; label: string }[] = [
  { id: 'wishlist', label: 'Wishlist' },
  { id: 'planned', label: 'Planned' },
  { id: 'visited', label: 'Visited' },
  { id: 'favourite', label: 'Favourite' },
  { id: 'trips', label: 'Trips' },
  { id: 'adventures', label: 'Adventures' },
  { id: 'photos', label: 'Photos' },
];

/** Which layer toggle controls a marker. */
export function markerLayer(marker: Marker): MapLayer {
  if (marker.kind === 'trip') return 'trips';
  if (marker.kind === 'adventure') return 'adventures';
  if (marker.kind === 'photo') return 'photos';
  return (marker.status as PlaceStatus) ?? 'wishlist';
}

export const MARKER_KIND_COLORS: Record<Exclude<MarkerKind, 'place'>, string> = {
  trip: '--primary',
  adventure: '--accent',
  photo: '--text-muted',
};

export function markerColor(marker: Marker): string {
  return marker.kind === 'place'
    ? PLACE_STATUS_COLORS[(marker.status as PlaceStatus) ?? 'wishlist'] ?? '--primary'
    : MARKER_KIND_COLORS[marker.kind];
}

// ---- trips (U2) ----------------------------------------------------------------------------------

export type TripStatus = 'draft' | 'planning' | 'booked' | 'active' | 'completed';
export type RouteMode = 'driving' | 'walking' | 'cycling' | 'transit';

export const TRIP_STATUS_LABELS: Record<TripStatus, string> = {
  draft: 'Draft',
  planning: 'Planning',
  booked: 'Booked',
  active: 'Active',
  completed: 'Completed',
};

export const ROUTE_MODES: readonly { id: RouteMode; label: string }[] = [
  { id: 'driving', label: 'Driving' },
  { id: 'walking', label: 'Walking' },
  { id: 'cycling', label: 'Cycling' },
  { id: 'transit', label: 'Transit' },
];

export interface TripSummary {
  id: string;
  name: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  dates_tentative: boolean;
  status: TripStatus;
  cover_photo_id: string | null;
  notes: string | null;
  confirmed_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TripListItem extends TripSummary {
  place_count: number;
}

export interface ItineraryItem {
  id: string;
  day_id: string;
  position: number;
  place_id: string | null;
  title: string;
  start_time: string | null;
  end_time: string | null;
  transport: string | null;
  accommodation: string | null;
  notes: string | null;
  links: string[];
}

export interface ItineraryDay {
  id: string;
  day_index: number;
  day_date: string | null;
  title: string | null;
  notes: string | null;
  items: ItineraryItem[];
}

export interface TripPlace {
  id: string;
  name: string;
  lat: number;
  lng: number;
  status: PlaceStatus;
  external_place_id: string | null;
}

export interface Stop {
  place_id: string;
  name: string;
  lat: number;
  lng: number;
}

export interface Route {
  id: string;
  name: string;
  source: 'google' | 'user_drawn' | 'gpx' | 'straight_line';
  mode: RouteMode;
  distance_m: number;
  duration_s: number | null;
  polyline: string;
  elevation_gain_m: number | null;
  elevation_loss_m: number | null;
  fallback_reason: string | null;
  trip_id: string | null;
  adventure_id: string | null;
  is_stale: boolean;
}

export interface RouteDetail extends Route {
  points: [number, number][];
  elevation_profile: number[] | null;
}

export interface TripDetail {
  trip: TripSummary;
  days: ItineraryDay[];
  places: TripPlace[];
  stops: Stop[];
  route: Route | null;
}

export interface TripCreate {
  name: string;
  start_date?: string | null;
  end_date?: string | null;
}

export type TripUpdate = Partial<Pick<TripSummary, 'name' | 'description' | 'start_date' | 'end_date' | 'dates_tentative' | 'notes'>>;

export type ItemUpdate = Partial<Omit<ItineraryItem, 'id' | 'day_id' | 'position'>>;

export function formatDistance(meters: number): string {
  return meters >= 1000 ? `${(meters / 1000).toFixed(meters >= 100_000 ? 0 : 1)} km` : `${Math.round(meters)} m`;
}

export function formatDuration(seconds: number | null): string | null {
  if (seconds == null) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  return h ? `${h} h ${m} min` : `${m} min`;
}

// ---- adventures (U3) -----------------------------------------------------------------------------

export type AdventureKind = 'trek' | 'hike' | 'road_trip' | 'camping' | 'cycling' | 'expedition';
export type Difficulty = 'easy' | 'moderate' | 'hard' | 'expert';
export type WaypointKind = 'start' | 'camp' | 'summit' | 'water' | 'viewpoint' | 'end' | 'other';

export const ADVENTURE_KINDS: readonly { id: AdventureKind; label: string }[] = [
  { id: 'trek', label: 'Trek' },
  { id: 'hike', label: 'Hike' },
  { id: 'road_trip', label: 'Road trip' },
  { id: 'camping', label: 'Camping' },
  { id: 'cycling', label: 'Cycling' },
  { id: 'expedition', label: 'Expedition' },
];
export const DIFFICULTIES: readonly Difficulty[] = ['easy', 'moderate', 'hard', 'expert'];
export const WAYPOINT_KINDS: readonly WaypointKind[] = ['start', 'camp', 'summit', 'water', 'viewpoint', 'end', 'other'];

export interface Adventure {
  id: string;
  name: string;
  kind: AdventureKind;
  difficulty: Difficulty | null;
  trip_id: string | null;
  start_date: string | null;
  end_date: string | null;
  route_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdventureWaypoint {
  id?: string;
  position?: number;
  lat: number;
  lng: number;
  name: string;
  kind: WaypointKind;
  elevation_m: number | null;
}

export interface AdventureDetail {
  adventure: Adventure;
  waypoints: AdventureWaypoint[];
  route: Route | null;
  route_points: [number, number][];
  elevation_profile: number[] | null;
}

export type AdventureUpdate = Partial<Pick<Adventure, 'name' | 'kind' | 'difficulty' | 'trip_id' | 'start_date' | 'end_date' | 'notes'>>;

export interface GpxPreview {
  name: string | null;
  point_count: number;
  points: [number, number][];
  distance_m: number;
  elevation_gain_m: number | null;
  elevation_loss_m: number | null;
  has_elevation: boolean;
  has_time: boolean;
  start_time: string | null;
  end_time: string | null;
  waypoints: { name: string; lat: number; lng: number; elevation: number | null }[];
}

// ---- memories + world (U4) -----------------------------------------------------------------------

export interface TravelPhoto {
  id: string;
  file_id: string;
  lat: number | null;
  lng: number | null;
  location_source: 'exif' | 'manual' | null;
  taken_at: string | null;
  caption: string | null;
  place_id: string | null;
  trip_id: string | null;
  day_id: string | null;
  adventure_id: string | null;
  journal_entry_id: string | null;
  created_at: string;
}

export interface PhotoMeta {
  lat?: number | null;
  lng?: number | null;
  location_source?: 'exif' | 'manual' | null;
  taken_at?: string | null;
  caption?: string | null;
  place_id?: string | null;
  trip_id?: string | null;
  adventure_id?: string | null;
  journal_entry_id?: string | null;
}

export interface JournalEntry {
  id: string;
  entry_date: string;
  title: string;
  content: string;
  trip_id: string | null;
  place_id: string | null;
  adventure_id: string | null;
  route_id: string | null;
  created_at: string;
  updated_at: string;
}

export type JournalInput = Pick<JournalEntry, 'entry_date' | 'title' | 'content'> &
  Partial<Pick<JournalEntry, 'trip_id' | 'place_id' | 'adventure_id' | 'route_id'>>;

export interface WorldOverview {
  markers: Marker[];
  counts: {
    wishlist: number;
    planned: number;
    visited: number;
    favourite: number;
    trips: number;
    completed_trips: number;
    adventures: number;
    photos: number;
  };
}

// ---- maps usage (U5) -----------------------------------------------------------------------------

export interface SkuUsage {
  sku: string;
  label: string;
  requests: number;
  blocked: number;
  free_units: number;
  pct_of_free: number;
  estimated_cost_usd: string;
  level: UsageLevel;
}

export interface BudgetStatus {
  protection_enabled: boolean;
  budget_amount: string;
  warning_amount: string;
  currency: string;
  spent_usd: string;
  spent_in_budget_currency: string | null;
  pct_of_budget: number | null;
  level: UsageLevel;
  non_essential_blocked: boolean;
}

export interface UsageSummary {
  month: string;
  skus: SkuUsage[];
  total_estimated_cost_usd: string;
  budget: BudgetStatus;
  fx_rates: Record<string, number>;
  pricing_last_reviewed_at: string | null;
  pricing_review_due: boolean;
}

export interface MapsSettings {
  protection_enabled: boolean;
  budget_amount: string;
  warning_amount: string;
  budget_currency: string;
  stop_at_free_tier: boolean;
  fx_rates: Record<string, number>;
  pricing_last_reviewed_at: string | null;
}

export interface PricingRow {
  sku: string;
  label: string;
  unit_price_usd_per_1000: string;
  free_monthly_units: number;
  active: boolean;
}

export const USAGE_LEVEL_LABELS: Record<UsageLevel, string> = {
  ok: 'OK',
  info: 'Informational',
  warning: 'Warning',
  high: 'High',
  critical: 'Critical',
  limit: 'Limit',
};
