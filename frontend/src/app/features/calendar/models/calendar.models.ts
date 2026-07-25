export type EventCategory = 'personal' | 'task' | 'running' | 'bill' | 'learning';
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
