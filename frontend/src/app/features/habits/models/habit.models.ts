export type HabitFrequency = 'daily' | 'weekly' | 'monthly';

export interface HabitLog {
  id: string;
  log_date: string;
  created_at: string;
}

export interface HabitStats {
  streak: number;
  completion_rate: number;
  total_logs: number;
  missed_periods: number;
  recent_logs: HabitLog[];
}

export interface Habit {
  id: string;
  name: string;
  description: string | null;
  frequency: HabitFrequency;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  completed_today: boolean;
  streak: number;
  completion_rate: number;
  stats: HabitStats;
  logs: HabitLog[];
}

export interface HabitListItem {
  id: string;
  name: string;
  frequency: HabitFrequency;
  is_active: boolean;
  completed_today: boolean;
  streak: number;
  completion_rate: number;
  updated_at: string;
}

export interface HabitCreate {
  name: string;
  description?: string | null;
  frequency?: HabitFrequency;
}

export interface HabitUpdate {
  name?: string;
  description?: string | null;
  frequency?: HabitFrequency;
  is_active?: boolean;
}

export const HABIT_FREQUENCIES: { value: HabitFrequency; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];
