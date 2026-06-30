export type EventCategory = 'personal' | 'task' | 'running' | 'bill' | 'learning';
export type EventRecurrence = 'none' | 'daily' | 'weekly' | 'monthly';

export interface CalendarEvent {
  id: string;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string | null;
  all_day: boolean;
  category: EventCategory;
  recurrence: EventRecurrence;
  location: string | null;
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
  location: string | null;
}

export interface EventCreate {
  title: string;
  description?: string | null;
  starts_at: string;
  ends_at?: string | null;
  all_day?: boolean;
  category?: EventCategory;
  recurrence?: EventRecurrence;
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
];
