export type RoutineArea = string;
export type RoutineCategory = string;

export interface RoutineBlock {
  id: string;
  title: string;
  start_time: string; // HH:MM:SS
  end_time: string;
  area: RoutineArea;
  category: RoutineCategory;
  notes: string | null;
  sort_order: number;
  habit_ids?: string[];
  habits?: { id: string; name: string }[];
}

export interface RoutineBlockInput {
  title: string;
  start_time: string; // HH:MM or HH:MM:SS
  end_time: string;
  area: RoutineArea;
  category: RoutineCategory;
  notes?: string | null;
  sort_order?: number;
  habit_ids?: string[];
}

export interface RoutineListItem {
  id: string;
  name: string;
  days_of_week: number[];
  timezone: string;
  start_date?: string | null;
  end_date?: string | null;
  is_active: boolean;
  block_count: number;
  updated_at: string;
}

export interface Routine {
  id: string;
  name: string;
  description: string | null;
  days_of_week: number[];
  timezone: string;
  start_date: string | null;
  end_date: string | null;
  skip_dates: string[];
  is_active: boolean;
  blocks: RoutineBlock[];
  created_at: string;
  updated_at: string;
}

export interface RoutineCreate {
  name: string;
  description?: string | null;
  days_of_week: number[];
  timezone?: string;
  start_date: string;
  end_date?: string | null;
  skip_dates?: string[];
  blocks: RoutineBlockInput[];
}

export interface RoutineUpdate {
  name?: string;
  description?: string | null;
  days_of_week?: number[];
  timezone?: string;
  start_date?: string | null;
  end_date?: string | null;
  skip_dates?: string[];
  is_active?: boolean;
  blocks?: RoutineBlockInput[];
}

export const ROUTINE_AREAS: { value: RoutineArea; label: string }[] = [
  { value: 'dsa', label: 'DSA' },
  { value: 'gym', label: 'Gym' },
  { value: 'running', label: 'Running' },
  { value: 'learning', label: 'Learning' },
  { value: 'communication', label: 'Communication' },
  { value: 'book', label: 'Book' },
  { value: 'other', label: 'Other' },
];

export const ROUTINE_CATEGORIES: { value: RoutineCategory; label: string }[] = [
  { value: 'personal', label: 'Personal' },
  { value: 'learning', label: 'Learning' },
  { value: 'running', label: 'Running' },
  { value: 'task', label: 'Task' },
  { value: 'bill', label: 'Bill' },
];

export const WEEKDAYS: { value: number; label: string; short: string }[] = [
  { value: 0, label: 'Monday', short: 'Mon' },
  { value: 1, label: 'Tuesday', short: 'Tue' },
  { value: 2, label: 'Wednesday', short: 'Wed' },
  { value: 3, label: 'Thursday', short: 'Thu' },
  { value: 4, label: 'Friday', short: 'Fri' },
  { value: 5, label: 'Saturday', short: 'Sat' },
  { value: 6, label: 'Sunday', short: 'Sun' },
];

/** Map life area → default calendar category */
export function defaultCategoryForArea(area: string): string {
  switch (area) {
    case 'dsa':
    case 'learning':
    case 'book':
      return 'learning';
    case 'running':
      return 'running';
    case 'gym':
    case 'communication':
    case 'other':
    default:
      return 'personal';
  }
}

export function formatTimeLabel(t: string): string {
  // Accept HH:MM:SS or HH:MM
  return t.length >= 5 ? t.slice(0, 5) : t;
}

export function formatDaysLabel(days: number[]): string {
  if (days.length === 7) return 'Every day';
  if (days.length === 5 && [0, 1, 2, 3, 4].every((d) => days.includes(d))) return 'Weekdays';
  if (days.length === 2 && days.includes(5) && days.includes(6)) return 'Weekends';
  return days
    .slice()
    .sort((a, b) => a - b)
    .map((d) => WEEKDAYS.find((w) => w.value === d)?.short ?? String(d))
    .join(', ');
}
