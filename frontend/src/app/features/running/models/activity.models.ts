export type ImportRange = '12m' | 'all';

/** How many months a Garmin API sync reads back. */
export type GarminSyncMonths = 1 | 3 | 6 | 9 | 12;

/** How a sync-log entry started: files the user uploaded, or a pull from the Garmin Personal API. */
export type ImportOrigin = 'upload' | 'sync';

export type ImportStatus = 'queued' | 'running' | 'finished' | 'failed' | 'interrupted';

export interface ImportFileError {
  name: string;
  reason: string;
}

export interface ImportJob {
  id: string;
  status: ImportStatus;
  /** API syncs: 'recent' re-reads only the last few days; '1m'…'12m' reads that many months back. */
  range_mode: ImportRange | 'recent' | `${GarminSyncMonths}m`;
  origin: ImportOrigin;
  files_found: number;
  created: number;
  duplicates: number;
  outside_range: number;
  not_activity: number;
  failed: number;
  runs_created: number;
  runs_matched: number;
  /** Days of health data an API sync stored. */
  health_days: number;
  errors: ImportFileError[];
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ImportedSummary {
  activities: number;
  runs_created: number;
  runs_merged_into_manual: number;
  /** Days of health data an import stored (data entered by hand is not counted). */
  health_days: number;
}

export interface DeleteImportedResult {
  activities_deleted: number;
  runs_deleted: number;
  runs_restored: number;
  races_detached: number;
  files_deleted: number;
  health_days_deleted: number;
}

export interface ActivityLap {
  index: number;
  start_offset_s: number;
  duration_s: number;
  distance_m: number;
  avg_hr: number | null;
  avg_cadence: number | null;
  elevation_gain_m: number | null;
}

export interface ActivitySplit {
  index: number;
  distance_m: number;
  duration_s: number;
  pace_s_per_km: number | null;
  avg_hr: number | null;
  elevation_change_m: number | null;
  avg_cadence: number | null;
}

export interface ActivityDetail {
  id: string;
  source: string;
  sport: string;
  start_time_utc: string;
  timezone: string | null;
  elapsed_seconds: number;
  timer_seconds: number;
  distance_m: number;
  elevation_gain_m: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  avg_cadence: number | null;
  max_speed_mps: number | null;
  calories: number | null;
  device: string | null;
  training_effect_aerobic: number | null;
  training_effect_anaerobic: number | null;
  laps: ActivityLap[];
  splits: ActivitySplit[];
  has_route: boolean;
  has_series: boolean;
  has_original_file: boolean;
}

export interface ActivitySeries {
  sample_count: number;
  time_s: number[];
  distance_m: (number | null)[] | null;
  heart_rate: (number | null)[] | null;
  cadence: (number | null)[] | null;
  altitude_m: (number | null)[] | null;
  speed_mps: (number | null)[] | null;
  /** [latitude, longitude] pairs. */
  route: [number, number][];
}
