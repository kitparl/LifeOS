/** Date labels for news. Timestamps arrive in UTC and are shown in the user's local timezone. */

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

function startOfLocalDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

/** Whole local calendar days from `from` to `to` (negative when `to` is earlier). */
function calendarDaysBetween(from: Date, to: Date): number {
  return Math.round((startOfLocalDay(to) - startOfLocalDay(from)) / DAY);
}

function plural(n: number, unit: string): string {
  return `${n} ${unit}${n === 1 ? '' : 's'}`;
}

/** "2 minutes ago", "1 hour ago", "Yesterday", "Sep 25, 2026". */
export function relativeTime(iso: string | null, now: Date = new Date()): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  const diff = now.getTime() - date.getTime();
  if (diff < MINUTE) return 'Just now';
  if (diff < HOUR) return `${plural(Math.floor(diff / MINUTE), 'minute')} ago`;
  if (calendarDaysBetween(date, now) === 0) return `${plural(Math.floor(diff / HOUR), 'hour')} ago`;
  if (calendarDaysBetween(date, now) === 1) return 'Yesterday';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

/** Full local date and time for the article page. */
export function fullDateTime(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

/** "Expires today" / "Expires tomorrow" / "Expires in 12 days". Never negative. */
export function expiryLabel(expiresIso: string, now: Date = new Date()): string {
  const days = Math.max(0, calendarDaysBetween(now, new Date(expiresIso)));
  if (days === 0) return 'Expires today';
  if (days === 1) return 'Expires tomorrow';
  return `Expires in ${days} days`;
}

/** "Saved today" / "Saved yesterday" / "Saved 5 days ago". */
export function savedAgoLabel(savedIso: string, now: Date = new Date()): string {
  const days = Math.max(0, calendarDaysBetween(new Date(savedIso), now));
  if (days === 0) return 'Saved today';
  if (days === 1) return 'Saved yesterday';
  return `Saved ${days} days ago`;
}

/** True when the article expires within `days` local calendar days (drives the "expiring soon" style). */
export function expiresSoon(expiresIso: string, now: Date = new Date(), days = 3): boolean {
  return calendarDaysBetween(now, new Date(expiresIso)) <= days;
}
