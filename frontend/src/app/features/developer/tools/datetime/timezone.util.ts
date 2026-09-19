import { extractWallClockParts } from '../../shared/datetime-parse.util';

const FALLBACK_ZONES = ['UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Europe/Berlin', 'Asia/Kolkata', 'Asia/Tokyo', 'Australia/Sydney'];

export interface TimezonePreset {
  label: string;
  from: string;
  to: string;
}

export const TIMEZONE_PRESETS: TimezonePreset[] = [
  { label: 'UTC → IST', from: 'UTC', to: 'Asia/Kolkata' },
  { label: 'IST → UTC', from: 'Asia/Kolkata', to: 'UTC' },
  { label: 'UTC → EST', from: 'UTC', to: 'America/New_York' },
  { label: 'UTC → PST', from: 'UTC', to: 'America/Los_Angeles' },
  { label: 'Local → UTC', from: Intl.DateTimeFormat().resolvedOptions().timeZone, to: 'UTC' },
  { label: 'UTC → Local', from: 'UTC', to: Intl.DateTimeFormat().resolvedOptions().timeZone },
];

export function listTimeZones(): string[] {
  const supportedValuesOf = (Intl as unknown as { supportedValuesOf?: (key: string) => string[] }).supportedValuesOf;
  try {
    return supportedValuesOf ? supportedValuesOf('timeZone') : FALLBACK_ZONES;
  } catch {
    return FALLBACK_ZONES;
  }
}

function formatInZone(date: Date, timeZone: string): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date);
  const get = (type: string): string => parts.find((p) => p.type === type)?.value ?? '00';
  return `${get('year')}-${get('month')}-${get('day')} ${get('hour') === '24' ? '00' : get('hour')}:${get('minute')}:${get('second')}`;
}

/**
 * Interprets a pasted/typed date-time string's wall-clock value as local time in `timeZone`
 * (any embedded zone/offset in the input itself is ignored — `timeZone` is authoritative) and
 * returns the equivalent UTC instant.
 */
function zonedTimeToUtc(dateTimeLocal: string, timeZone: string): Date {
  const wallClock = extractWallClockParts(dateTimeLocal);
  const guessUtc = new Date(wallClock + 'Z');
  if (isNaN(guessUtc.getTime())) throw new Error('Could not parse that date/time.');
  const asIfInZone = new Date(formatInZone(guessUtc, timeZone).replace(' ', 'T') + 'Z');
  const diff = guessUtc.getTime() - asIfInZone.getTime();
  return new Date(guessUtc.getTime() + diff);
}

export function convertTimezone(dateTimeLocal: string, fromZone: string, toZone: string): string {
  const utc = zonedTimeToUtc(dateTimeLocal, fromZone);
  return formatInZone(utc, toZone);
}
