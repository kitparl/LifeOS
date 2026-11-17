/** Built-in categories plus any user-defined (free-text, lowercase) ones. */
export type EventCategory = string;
export type EventRecurrence = 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly';
export type EventKind = 'normal' | 'birthday' | 'immutable';

export interface CalendarEvent {
  id: string;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string | null;
  all_day: boolean;
  category: EventCategory;
  recurrence: EventRecurrence;
  event_kind?: EventKind;
  location: string | null;
  /** Owning module for synced events (e.g. 'running'); null for user-created. */
  source_module?: string | null;
  source_id?: string | null;
  /** Google Calendar-sourced event that cannot be edited here (one-way sync). */
  read_only?: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventListItem {
  id: string;
  title: string;
  starts_at: string;
  ends_at: string | null;
  all_day: boolean;
  category: EventCategory;
  recurrence: EventRecurrence;
  event_kind?: EventKind;
  location: string | null;
  source_module?: string | null;
  source_id?: string | null;
  /** Google Calendar-sourced event that cannot be edited here (one-way sync). */
  read_only?: boolean;
}

export interface EventCreate {
  title: string;
  description?: string | null;
  starts_at: string;
  ends_at?: string | null;
  all_day?: boolean;
  category?: EventCategory;
  recurrence?: EventRecurrence;
  event_kind?: EventKind;
  location?: string | null;
}

export interface EventUpdate {
  title?: string;
  description?: string | null;
  starts_at?: string;
  ends_at?: string | null;
  all_day?: boolean;
  category?: EventCategory;
  recurrence?: EventRecurrence;
  event_kind?: EventKind;
  location?: string | null;
}

export const EVENT_CATEGORIES: { value: EventCategory; label: string }[] = [
  { value: 'personal', label: 'Personal' },
  { value: 'task', label: 'Task' },
  { value: 'running', label: 'Running' },
  { value: 'bill', label: 'Bill' },
  { value: 'learning', label: 'Learning' },
];

export const EVENT_RECURRENCE: { value: EventRecurrence; label: string }[] = [
  { value: 'none', label: 'None' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
];

export const EVENT_KINDS: { value: EventKind; label: string }[] = [
  { value: 'normal', label: 'Normal' },
  { value: 'birthday', label: 'Birthday (yearly reminders)' },
  { value: 'immutable', label: 'Immutable (long reminder ladder)' },
];

/** Category → display color for the built-in categories */
export const CATEGORY_COLORS: Record<string, string> = {
  personal: '#3b82f6',
  task: '#8b5cf6',
  running: '#22c55e',
  bill: '#ef4444',
  learning: '#f59e0b',
};

/** Palette for custom categories; picked deterministically from the name. */
const CUSTOM_CATEGORY_PALETTE = ['#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16', '#a855f7', '#0ea5e9'];

export function categoryColor(category: EventCategory): string {
  const known = CATEGORY_COLORS[category];
  if (known) return known;
  let hash = 0;
  for (const ch of category) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return CUSTOM_CATEGORY_PALETTE[hash % CUSTOM_CATEGORY_PALETTE.length];
}

export function categoryLabel(category: EventCategory): string {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

export function normalizeCategory(raw: string): string {
  return raw.trim().toLowerCase().slice(0, 32);
}
