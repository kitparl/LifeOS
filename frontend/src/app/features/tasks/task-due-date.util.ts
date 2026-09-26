import { localIsoDate, pad2 } from '../../core/utils/date';
/** Split API ISO datetime into separate date + optional time fields. */
export function splitDueDate(iso: string | null): { date: string; time: string } {
  if (!iso) {
    return { date: '', time: '' };
  }
  const d = new Date(iso);
  const date = localIsoDate(d);
  const h = d.getHours();
  const m = d.getMinutes();
  // Date-only tasks are stored at 12:00 local.
  const time = h === 12 && m === 0 ? '' : `${pad2(h)}:${pad2(m)}`;
  return { date, time };
}

/** Combine date input + optional time into ISO for the API. */
export function combineDueDate(date: string, time: string): string | null {
  const trimmed = date.trim();
  if (!trimmed) {
    return null;
  }
  const timePart = time.trim() || '12:00';
  return new Date(`${trimmed}T${timePart}:00`).toISOString();
}
