export type RaceDistanceType = '5k' | '10k' | '15k' | 'half_marathon' | 'marathon' | 'other';

export interface Run {
  id: string;
  run_date: string;
  distance_km: number;
  duration_seconds: number;
  pace_min_per_km: number;
  weather: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface RunListItem {
  id: string;
  run_date: string;
  distance_km: number;
  duration_seconds: number;
  pace_min_per_km: number;
  weather: string | null;
  updated_at: string;
}

export interface RunCreate {
  run_date: string;
  distance_km: number;
  duration_seconds: number;
  weather?: string | null;
  notes?: string | null;
}

export interface RunUpdate {
  run_date?: string;
  distance_km?: number;
  duration_seconds?: number;
  weather?: string | null;
  notes?: string | null;
}

export interface RaceEvent {
  id: string;
  name: string;
  race_date: string;
  distance_type: RaceDistanceType;
  distance_km: number | null;
  location: string | null;
  registered: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface RaceCreate {
  name: string;
  race_date: string;
  distance_type?: RaceDistanceType;
  distance_km?: number | null;
  location?: string | null;
  registered?: boolean;
  notes?: string | null;
}

export interface RunningSettings {
  weekly_goal_km: number;
  target_marathon_date: string | null;
  target_half_marathon_date: string | null;
  target_marathon_name: string | null;
}

export interface PersonalBest {
  distance_type: string;
  label: string;
  run_id: string | null;
  run_date: string | null;
  distance_km: number | null;
  pace_min_per_km: number | null;
  duration_seconds: number | null;
}

export interface RunningStats {
  weekly_km: number;
  weekly_goal_km: number;
  total_runs: number;
  total_km: number;
  last_run_date: string | null;
  personal_bests: PersonalBest[];
}

export const RACE_DISTANCES: { value: RaceDistanceType; label: string }[] = [
  { value: '5k', label: '5K' },
  { value: '10k', label: '10K' },
  { value: '15k', label: '15K' },
  { value: 'half_marathon', label: 'Half Marathon' },
  { value: 'marathon', label: 'Marathon' },
  { value: 'other', label: 'Other' },
];

export const WEATHER_OPTIONS = ['sunny', 'cloudy', 'rain', 'cold', 'hot', 'windy'];

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function formatPace(pace: number): string {
  const mins = Math.floor(pace);
  const secs = Math.round((pace - mins) * 60);
  return `${mins}:${secs.toString().padStart(2, '0')} /km`;
}

export function durationToSeconds(hours: number, minutes: number, seconds: number): number {
  return hours * 3600 + minutes * 60 + seconds;
}

export function secondsToParts(total: number): { hours: number; minutes: number; seconds: number } {
  return {
    hours: Math.floor(total / 3600),
    minutes: Math.floor((total % 3600) / 60),
    seconds: total % 60,
  };
}
