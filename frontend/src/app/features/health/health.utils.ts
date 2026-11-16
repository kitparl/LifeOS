import { HealthDay, MetricInfo, MetricPoint, TrendMarker } from './models/health.models';

const pad2 = (n: number): string => String(n).padStart(2, '0');

/** Minutes after midnight as HH:MM. */
export function minutesToClock(minutes: number): string {
  const m = ((Math.round(minutes) % 1440) + 1440) % 1440;
  return `${pad2(Math.floor(m / 60))}:${pad2(m % 60)}`;
}

/** "HH:MM" as minutes after midnight; null when it is not a valid time. */
export function clockToMinutes(value: string): number | null {
  const match = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(value.trim());
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

/** Minutes of sleep as "7 h 12 min" (or "45 min"); an em dash when unknown. */
export function sleepLabel(minutes: number | null | undefined): string {
  if (minutes == null || !Number.isFinite(minutes)) return '—';
  const total = Math.round(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  return h > 0 ? `${h} h ${pad2(m)} min` : `${m} min`;
}

type MetricShape = Pick<MetricInfo, 'key' | 'unit'> & Partial<Pick<MetricInfo, 'kind'>>;

/** A value the way a person reads it: clock times as HH:MM, sleep as hours and minutes, others with their unit. */
export function formatMetric(metric: MetricShape, value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—';
  if (metric.kind === 'clock') return minutesToClock(value);
  if (metric.unit === 'min' && metric.key.startsWith('sleep_')) return sleepLabel(value);
  const text = Number.isInteger(value) ? String(value) : String(Number(value.toFixed(1)));
  return metric.unit ? `${text} ${metric.unit}` : text;
}

export function markerLabel(marker: TrendMarker | null): string {
  switch (marker) {
    case 'up':
      return 'above your 30-day average';
    case 'down':
      return 'below your 30-day average';
    case 'flat':
      return 'in line with your 30-day average';
    default:
      return '';
  }
}

export function markerSymbol(marker: TrendMarker | null): string {
  return marker === 'up' ? '▲' : marker === 'down' ? '▼' : marker === 'flat' ? '●' : '';
}

export interface ChartDot {
  index: number;
  value: number;
}

/** Runs of consecutive days that have a value; a missing day ends a run, so a chart draws a gap there. */
export function chartSegments(points: MetricPoint[]): ChartDot[][] {
  const segments: ChartDot[][] = [];
  let current: ChartDot[] = [];
  points.forEach((p, index) => {
    if (p.value == null) {
      if (current.length) segments.push(current);
      current = [];
    } else {
      current.push({ index, value: p.value });
    }
  });
  if (current.length) segments.push(current);
  return segments;
}

export interface DayPayload {
  values: Record<string, number>;
  /** Labels of fields whose text is not a valid number or time. */
  invalid: string[];
}

/** Only the fields that were filled in; clock fields are converted to minutes. Blank means "leave as it is". */
export function buildDayPayload(raw: Record<string, string>, catalogue: MetricInfo[]): DayPayload {
  const values: Record<string, number> = {};
  const invalid: string[] = [];
  for (const metric of catalogue) {
    const text = (raw[metric.key] ?? '').trim();
    if (!text) continue;
    if (metric.kind === 'clock') {
      const minutes = clockToMinutes(text);
      if (minutes === null) invalid.push(metric.label);
      else values[metric.key] = minutes;
    } else {
      const number = Number(text.replace(',', '.'));
      if (!Number.isFinite(number)) invalid.push(metric.label);
      else values[metric.key] = number;
    }
  }
  return { values, invalid };
}

/** The text of a form field for a stored value (clock values as HH:MM). */
export function fieldText(metric: MetricInfo, value: number | undefined): string {
  if (value == null) return '';
  return metric.kind === 'clock' ? minutesToClock(value) : String(value);
}

/** Server validation messages arrive as "Value error, <sentence>"; show only the sentence. */
export function cleanMessage(message: string): string {
  return message.replace(/^Value error,\s*/i, '');
}

/** Values of a day that were entered by hand (a day form edits only these). */
export function manualValues(day: HealthDay): Record<string, number> {
  return Object.fromEntries(Object.entries(day.values).filter(([key]) => day.sources[key] === 'manual'));
}
