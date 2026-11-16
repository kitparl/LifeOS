export type TimelineSourceKey =
  | 'calendar'
  | 'running'
  | 'travel'
  | 'tasks'
  | 'journal'
  | 'finance'
  | 'wishlist'
  | 'routines';

/** Registry entry served by `GET /timeline/sources` (labels + defaults live on the backend). */
export interface TimelineSource {
  key: TimelineSourceKey;
  label: string;
  default_enabled: boolean;
}

export interface TimelineItem {
  id: string;
  source: TimelineSourceKey;
  kind: string;
  title: string;
  subtitle: string | null;
  starts_at: string;
  ends_at: string | null;
  all_day: boolean;
  status: string | null;
  route: string | null;
}

export type TimelineZoom = 'week' | 'month' | 'quarter';

export const TIMELINE_ZOOMS: readonly { value: TimelineZoom; label: string }[] = [
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' },
  { value: 'quarter', label: 'Quarter' },
];

/** Presentation only — colors are theme tokens so light/dark both work. */
export const TIMELINE_SOURCE_STYLE: Record<TimelineSourceKey, { icon: string; color: string }> = {
  calendar: { icon: 'calendar-days', color: 'var(--info)' },
  running: { icon: 'footprints', color: 'var(--success)' },
  travel: { icon: 'map', color: 'var(--accent)' },
  tasks: { icon: 'list-todo', color: 'var(--primary)' },
  journal: { icon: 'book-open', color: 'var(--favorite)' },
  finance: { icon: 'wallet', color: 'var(--danger)' },
  wishlist: { icon: 'star', color: 'var(--warning)' },
  routines: { icon: 'refresh-cw', color: 'var(--text-muted)' },
};
