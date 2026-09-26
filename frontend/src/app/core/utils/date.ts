/**
 * Shared "now/today" and date-string helpers.
 *
 * `utc*` helpers read the UTC calendar (`toISOString`); `local*` helpers read the browser's
 * calendar. Call sites keep whichever one they used before — they are not interchangeable
 * around midnight.
 */

export function pad2(value: number): string {
  return String(value).padStart(2, '0');
}

/** `YYYY-MM-DD` of `date` on the UTC calendar. */
export function utcIsoDate(date: Date = new Date()): string {
  return date.toISOString().slice(0, 10);
}

/** `YYYY-MM-DDTHH:mm` of `date` in UTC. */
export function utcIsoMinute(date: Date): string {
  return date.toISOString().slice(0, 16);
}

/** `YYYY-MM-DD` of `date` on the local calendar (the value a `<input type="date">` expects). */
export function localIsoDate(date: Date = new Date()): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

/** Local `YYYY-MM-DDTHH:mm`, the value a native `<input type="datetime-local">` expects. */
export function toDatetimeLocalValue(date: Date): string {
  return `${localIsoDate(date)}T${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

/** `YYYY-MM` for a 1-based month. */
export function yearMonthKey(year: number, month: number): string {
  return `${year}-${pad2(month)}`;
}
