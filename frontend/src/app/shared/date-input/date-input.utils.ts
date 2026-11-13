import * as chrono from 'chrono-node/en';
import { localIsoDate, pad2, toDatetimeLocalValue, yearMonthKey } from '../../core/utils/date';

/**
 * Pure helpers behind `<app-date-input>`. Values use the exact strings the native inputs
 * produced, so forms and the API see no change:
 *   date `YYYY-MM-DD` · datetime `YYYY-MM-DDTHH:mm` · time `HH:mm` · month `YYYY-MM`.
 */
export type DateInputMode = 'date' | 'datetime' | 'time' | 'month';

/** Hour used when typed text names a day but no time ("tomorrow") in datetime mode. */
const DEFAULT_HOUR = 9;

/** One- or two-letter shortcuts typed then Enter. */
const ALIASES: Record<string, number> = { t: 0, tod: 0, tm: 1, tom: 1, y: -1, yd: -1 };

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;
const LOCAL_MINUTE = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?$/;
const TIME_ONLY = /^(\d{1,2}):(\d{2})(?::\d{2})?$/;
const MONTH_ONLY = /^(\d{4})-(\d{2})$/;
/** A full ISO timestamp with seconds or a zone, as the API returns (`2026-11-13T09:00:00Z`). */
const ISO_WITH_ZONE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$/;

export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function addDays(date: Date, days: number): Date {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

/** Adds months, clamping the day (31 Jan + 1 month = 28/29 Feb). */
export function addMonths(date: Date, months: number): Date {
  const next = new Date(date.getFullYear(), date.getMonth() + months, 1, date.getHours(), date.getMinutes());
  const lastDay = new Date(next.getFullYear(), next.getMonth() + 1, 0).getDate();
  next.setDate(Math.min(date.getDate(), lastDay));
  return next;
}

export function addMinutes(date: Date, minutes: number): Date {
  return new Date(date.getTime() + minutes * 60_000);
}

/** A stored value as a local `Date`; null for empty or unreadable values. */
export function valueToDate(value: string | null | undefined, mode: DateInputMode, today: Date = new Date()): Date | null {
  const text = (value ?? '').trim();
  if (!text) return null;
  let match: RegExpMatchArray | null;
  if ((match = text.match(DATE_ONLY))) return new Date(+match[1], +match[2] - 1, +match[3]);
  if ((match = text.match(LOCAL_MINUTE))) return new Date(+match[1], +match[2] - 1, +match[3], +match[4], +match[5]);
  if ((match = text.match(TIME_ONLY))) {
    return new Date(today.getFullYear(), today.getMonth(), today.getDate(), +match[1], +match[2]);
  }
  if ((match = text.match(MONTH_ONLY))) return new Date(+match[1], +match[2] - 1, 1);
  if (mode === 'time' || !ISO_WITH_ZONE.test(text)) return null;
  const parsed = new Date(text);
  return isNaN(parsed.getTime()) ? null : parsed;
}

/** A `Date` as the stored string for `mode`. */
export function dateToValue(date: Date, mode: DateInputMode): string {
  switch (mode) {
    case 'date':
      return localIsoDate(date);
    case 'datetime':
      return toDatetimeLocalValue(date);
    case 'time':
      return `${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
    case 'month':
      return yearMonthKey(date.getFullYear(), date.getMonth() + 1);
  }
}

const DISPLAY: Record<DateInputMode, Intl.DateTimeFormatOptions> = {
  date: { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' },
  datetime: { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true },
  time: { hour: 'numeric', minute: '2-digit', hour12: true },
  month: { month: 'long', year: 'numeric' },
};

/** What the field shows, e.g. "Fri, 13 Nov 2026" or "5:30 pm". Always re-parsable by {@link parseTyped}. */
export function displayDate(date: Date, mode: DateInputMode): string {
  return new Intl.DateTimeFormat('en-GB', DISPLAY[mode]).format(date);
}

/**
 * Free text typed into the field → a `Date`, or null if it can't be read.
 * Accepts the stored formats, shortcuts (`t`, `tm`, `y`) and plain English via chrono
 * ("tomorrow 5pm", "next fri", "25 dec", "in 2 hours"), reading numeric dates day-first (25/12).
 * `current` keeps the time of day when only a date is typed in datetime mode.
 */
export function parseTyped(text: string, mode: DateInputMode, current: Date | null, now: Date = new Date()): Date | null {
  const trimmed = text.trim();
  if (!trimmed) return null;

  const alias = ALIASES[trimmed.toLowerCase()];
  if (alias !== undefined && mode !== 'time') {
    return withTime(addDays(startOfDay(now), alias), mode, current, now, false);
  }

  const exact = valueToDate(trimmed, mode, now);
  if (exact) return mode === 'month' ? new Date(exact.getFullYear(), exact.getMonth(), 1) : exact;

  // No forwardDate: "25 dec" means the nearest one, which suits past entries (expenses, runs) and plans alike.
  const [result] = chrono.GB.parse(trimmed, now);
  if (!result) return null;
  const parsed = result.start.date();
  if (mode === 'month') return new Date(parsed.getFullYear(), parsed.getMonth(), 1);
  if (mode === 'date') return startOfDay(parsed);
  return withTime(parsed, mode, current, now, result.start.isCertain('hour'));
}

/** Gives a typed day a sensible time: the one typed, else the current value's, else 9:00. */
function withTime(date: Date, mode: DateInputMode, current: Date | null, now: Date, timeTyped: boolean): Date {
  if (mode === 'date' || timeTyped) return date;
  if (mode === 'time') return new Date(now.getFullYear(), now.getMonth(), now.getDate(), date.getHours(), date.getMinutes());
  const hours = current ? current.getHours() : DEFAULT_HOUR;
  const minutes = current ? current.getMinutes() : 0;
  return new Date(date.getFullYear(), date.getMonth(), date.getDate(), hours, minutes);
}

export type StepUnit = 'small' | 'large';

/**
 * Keyboard nudge: `+`/`-` move by a small step, PageUp/PageDown by a large one.
 * date/datetime: 1 day / 1 month · time: 15 min / 1 hour · month: 1 month / 1 year.
 */
export function stepDate(date: Date, mode: DateInputMode, unit: StepUnit, direction: 1 | -1): Date {
  switch (mode) {
    case 'time':
      return addMinutes(date, direction * (unit === 'small' ? 15 : 60));
    case 'month':
      return addMonths(date, direction * (unit === 'small' ? 1 : 12));
    default:
      return unit === 'small' ? addDays(date, direction) : addMonths(date, direction);
  }
}

export interface QuickPick {
  label: string;
  value: (now: Date, current: Date | null) => Date;
}

/** One-tap choices shown in the picker's footer. */
export const QUICK_PICKS: Record<DateInputMode, QuickPick[]> = {
  date: [
    { label: 'Today', value: (now) => startOfDay(now) },
    { label: 'Tomorrow', value: (now) => addDays(startOfDay(now), 1) },
    { label: 'Next week', value: (now) => addDays(startOfDay(now), 7) },
  ],
  datetime: [
    { label: 'Now', value: (now) => roundToMinutes(now, 5) },
    { label: 'In 1 hour', value: (now) => roundToMinutes(addMinutes(now, 60), 5) },
    { label: 'Tomorrow 9 AM', value: (now) => addMinutes(addDays(startOfDay(now), 1), DEFAULT_HOUR * 60) },
  ],
  time: [
    { label: 'Now', value: (now) => roundToMinutes(now, 5) },
    { label: '+1 hour', value: (now, current) => addMinutes(current ?? roundToMinutes(now, 5), 60) },
  ],
  month: [
    { label: 'This month', value: (now) => new Date(now.getFullYear(), now.getMonth(), 1) },
    { label: 'Last month', value: (now) => new Date(now.getFullYear(), now.getMonth() - 1, 1) },
  ],
};

export function roundToMinutes(date: Date, step: number): Date {
  const rounded = new Date(date);
  rounded.setSeconds(0, 0);
  rounded.setMinutes(Math.round(rounded.getMinutes() / step) * step);
  return rounded;
}

/** True when `date` falls outside the optional `[min, max]` stored values (compared at the mode's precision). */
export function outOfRange(date: Date, mode: DateInputMode, min: string, max: string): boolean {
  const value = dateToValue(date, mode);
  const lower = min ? dateToValue(valueToDate(min, mode) ?? date, mode) : '';
  const upper = max ? dateToValue(valueToDate(max, mode) ?? date, mode) : '';
  return (!!lower && value < lower) || (!!upper && value > upper);
}
