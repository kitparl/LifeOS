/** Shared trip plans: the plan document, the owner's share/version shapes and the public planner shapes. */

// ---- the plan document (same shape as backend `schemas/plan_document.py`) ----------------------

export type StopKind = 'stay' | 'food' | 'travel' | 'sightseeing' | 'rest' | 'other';

export interface PlanPlace {
  name: string;
  lat: number;
  lng: number;
  google_place_id?: string | null;
}

export interface PlanStop {
  /** Stable across copies, so a plan can be compared with the Original it started from. */
  id: string;
  title: string;
  kind: StopKind;
  place: PlanPlace | null;
  start_time: string | null;
  end_time: string | null;
  transport: string | null;
  stay: string | null;
  notes: string | null;
  links: string[];
}

export interface PlanDay {
  title: string | null;
  notes: string | null;
  stops: PlanStop[];
}

export interface PlanDocument {
  schema_version: 1;
  days: PlanDay[];
}

// ---- owner side ---------------------------------------------------------------------------------

export type ShareState = 'open' | 'locked' | 'revoked';
export type VersionKind = 'original' | 'plan' | 'owner' | 'backup';
export type VersionStatus = 'draft' | 'submitted';

export interface ShareContributor {
  id: string;
  kind: 'google' | 'name';
  display_name: string;
  google_email: string | null;
  removed: boolean;
  created_at: string;
  last_seen_at: string | null;
}

export interface TripShare {
  id: string;
  trip_id: string;
  code: string;
  url_path: string;
  state: ShareState;
  require_google: boolean;
  allowed_emails: string[];
  original_version_id: string | null;
  locked_version_id: string | null;
  created_at: string;
  locked_at: string | null;
  revoked_at: string | null;
  contributors: ShareContributor[];
}

export interface ShareSettingsUpdate {
  require_google?: boolean;
  allowed_emails?: string[];
}

export interface PlanSummary {
  days: number;
  stops: number;
  added: number;
  removed: number;
  changed: number;
  km: number;
}

export interface VersionRow {
  id: string;
  kind: VersionKind;
  label: string;
  status: VersionStatus;
  author_kind: 'owner' | 'contributor' | 'system';
  author_name: string;
  author_email: string | null;
  contributor_removed: boolean;
  is_locked: boolean;
  edited_since_sent: boolean;
  message: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  summary: PlanSummary;
}

export interface VersionDetail extends VersionRow {
  document: PlanDocument;
}

export interface ApplyResult {
  days: number;
  items: number;
  places_created: number;
  places_reused: number;
  backup_version_id: string;
  end_date: string | null;
  end_date_changed: boolean;
}

export interface LockResult {
  share: TripShare;
  applied: ApplyResult | null;
}

// ---- public planner -----------------------------------------------------------------------------

export interface PublicPlanView {
  trip: { name: string; description: string | null; start_date: string | null; end_date: string | null };
  owner_name: string;
  state: 'open' | 'locked';
  names_allowed: boolean;
  google_enabled: boolean;
  is_final: boolean;
  viewer_is_owner: boolean;
  /** Only for the signed-in owner: where to manage the plan in LifeOS. */
  manage_path: string | null;
  plan: PlanDocument;
  limits: { max_days: number; max_stops: number };
}

export interface ContributorMe {
  id: string;
  kind: 'google' | 'name';
  display_name: string;
}

export interface MyPlan {
  id: string;
  status: VersionStatus;
  revision: number;
  updated_at: string;
  submitted_at: string | null;
  edited_since_sent: boolean;
  document: PlanDocument;
}

export interface MyView {
  contributor: ContributorMe;
  plan: MyPlan | null;
}

export interface ShareSession extends MyView {
  token: string;
  expires_at: string;
}

export interface JoinResult extends ShareSession {
  device_secret: string;
}

export interface ResolvedLink {
  name: string | null;
  lat: number | null;
  lng: number | null;
  google_place_id: string | null;
}
