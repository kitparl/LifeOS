export type HealthRange = '7d' | '30d' | '90d' | '1y';

export type MeasurementKind = 'weight' | 'body_comp' | 'blood_pressure';

export type MetricKind = 'int' | 'float' | 'clock';

export interface MetricInfo {
  key: string;
  label: string;
  unit: string;
  group: string;
  kind: MetricKind;
  min: number;
  max: number;
  lower_is_better: boolean | null;
  today: boolean;
}

export interface HealthDay {
  day: string;
  values: Record<string, number>;
  /** Where each value came from: "manual" or an import source such as "garmin". */
  sources: Record<string, string>;
}

export type TrendMarker = 'up' | 'down' | 'flat';

export interface TodayMetric {
  key: string;
  label: string;
  unit: string;
  value: number | null;
  avg_7d: number | null;
  avg_30d: number | null;
  marker: TrendMarker | null;
  favourable: 'good' | 'bad' | null;
  needs_more_data: boolean;
}

export interface HealthToday {
  day: string | null;
  is_today: boolean;
  metrics: TodayMetric[];
}

export interface MetricPoint {
  day: string;
  value: number | null;
}

export interface MetricSeries {
  key: string;
  label: string;
  unit: string;
  range: HealthRange;
  start: string;
  end: string;
  points: MetricPoint[];
  rolling: MetricPoint[];
  average: number | null;
  minimum: number | null;
  maximum: number | null;
}

export interface SleepConsistency {
  nights: number;
  bed_time_sd_min: number | null;
  wake_time_sd_min: number | null;
}

export interface SleepResponse {
  range: HealthRange;
  start: string;
  end: string;
  nights: HealthDay[];
  consistency: SleepConsistency;
}

export interface Measurement {
  id: string;
  kind: MeasurementKind;
  measured_at: string;
  values: Record<string, number>;
  source: string;
}

export interface MeasurementCreate {
  kind: MeasurementKind;
  measured_at?: string | null;
  values: Record<string, number>;
}

export const HEALTH_RANGES: { value: HealthRange; label: string }[] = [
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: '90d', label: '90 days' },
  { value: '1y', label: '1 year' },
];

export const METRIC_GROUPS: { id: string; label: string }[] = [
  { id: 'sleep', label: 'Sleep' },
  { id: 'heart', label: 'Heart' },
  { id: 'stress', label: 'Stress and energy' },
  { id: 'activity', label: 'Activity' },
  { id: 'breathing', label: 'Breathing and oxygen' },
  { id: 'fitness', label: 'Fitness' },
];
