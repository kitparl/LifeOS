export type StickyNoteColor = 'yellow' | 'pink' | 'blue' | 'green' | 'purple' | 'orange' | 'gray';

export interface StickyNote {
  id: string;
  title: string | null;
  content: string | null;
  color: StickyNoteColor;
  is_pinned: boolean;
  order_index: number;
  note_month: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface StickyNoteMonth {
  month: string;
  note_count: number;
}

/** Matches STICKY_NOTES_PURGE_AFTER_DAYS in backend/app/modules/sticky_notes/service.py. */
export const STICKY_NOTES_PURGE_AFTER_DAYS = 60;

export const STICKY_NOTE_COLORS: { value: StickyNoteColor; label: string }[] = [
  { value: 'yellow', label: 'Yellow' },
  { value: 'pink', label: 'Pink' },
  { value: 'blue', label: 'Blue' },
  { value: 'green', label: 'Green' },
  { value: 'purple', label: 'Purple' },
  { value: 'orange', label: 'Orange' },
  { value: 'gray', label: 'Gray' },
];

/** First non-blank line of the content, used as a fallback display title. */
export function stickyNoteDisplayTitle(note: Pick<StickyNote, 'title' | 'content'>): string {
  if (note.title?.trim()) return note.title.trim();
  const firstLine = (note.content ?? '').split('\n').find((line) => line.trim().length > 0);
  return firstLine?.trim() ?? 'New note';
}

export function stickyNoteMonthLabel(month: string): string {
  const [year, m] = month.split('-').map(Number);
  return new Date(year, m - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}


/** Years with notes, the selected year, and the last 10 calendar years. */
export function stickyNoteYearOptions(
  noteMonths: Pick<StickyNoteMonth, 'month'>[],
  selectedYear: number,
  now = new Date(),
): number[] {
  const current = now.getFullYear();
  const years = new Set<number>();
  for (let year = current; year >= current - 10; year -= 1) years.add(year);
  years.add(selectedYear);
  for (const entry of noteMonths) {
    const year = Number(entry.month.slice(0, 4));
    if (Number.isFinite(year)) years.add(year);
  }
  return [...years].sort((a, b) => b - a);
}

const TAG_MAX_LENGTH = 40;
const TAG_INVALID_CHARS = /[^a-z0-9_-]/g;

/** Strips a leading '#', lowercases, trims, and drops disallowed characters. Mirrors backend normalize_tag(). */
export function normalizeTag(raw: string): string {
  const withoutHash = raw.trim().replace(/^#+/, '');
  return withoutHash.trim().toLowerCase().replace(TAG_INVALID_CHARS, '').slice(0, TAG_MAX_LENGTH);
}

/** Days left before a soft-deleted note is permanently purged (never negative). */
export function daysUntilPurge(deletedAt: string | null): number {
  if (!deletedAt) return STICKY_NOTES_PURGE_AFTER_DAYS;
  const expires = new Date(deletedAt).getTime() + STICKY_NOTES_PURGE_AFTER_DAYS * 24 * 60 * 60 * 1000;
  return Math.max(0, Math.ceil((expires - Date.now()) / (24 * 60 * 60 * 1000)));
}
