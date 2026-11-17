import { ChartPoint } from '../../shared/charts/chart-types';
import { ActivitySeries, ImportJob } from './models/activity.models';

export type ChartChannel = 'pace' | 'heart_rate' | 'altitude_m' | 'cadence';

/** Samples slower than this are standing still; they would make the pace chart spike. */
const MIN_MOVING_SPEED_MPS = 0.5;

export function isJobActive(job: Pick<ImportJob, 'status'> | null | undefined): boolean {
  return job?.status === 'queued' || job?.status === 'running';
}

/** Seconds per kilometre as "5:06 /km"; an em dash when unknown. */
export function paceLabel(secondsPerKm: number | null | undefined): string {
  if (secondsPerKm == null || !Number.isFinite(secondsPerKm) || secondsPerKm <= 0) return '—';
  const total = Math.round(secondsPerKm);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')} /km`;
}

/** A duration in seconds as m:ss or h:mm:ss. */
export function clockLabel(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return '—';
  const total = Math.round(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m);
  return `${h > 0 ? `${h}:` : ''}${mm}:${String(s).padStart(2, '0')}`;
}

function channelValues(series: ActivitySeries, channel: ChartChannel): (number | null)[] | null {
  if (channel === 'pace') {
    return (
      series.speed_mps?.map((v) => (v != null && v >= MIN_MOVING_SPEED_MPS ? 1000 / v / 60 : null)) ?? null
    );
  }
  return series[channel];
}

/**
 * Points for one chart: the value of the channel against distance in km
 * (elapsed minutes when the activity has no distance channel). Samples without a value are skipped.
 */
export function chartPoints(series: ActivitySeries, channel: ChartChannel): ChartPoint[] {
  const values = channelValues(series, channel);
  if (!values) return [];
  const points: ChartPoint[] = [];
  values.forEach((value, i) => {
    if (value == null || !Number.isFinite(value)) return;
    const km = series.distance_m?.[i];
    const label = km != null ? (km / 1000).toFixed(2) : (series.time_s[i] / 60).toFixed(1);
    points.push({ label, value });
  });
  return points;
}

export function rangeLabel(points: ChartPoint[], digits = 0): string {
  if (!points.length) return '';
  const values = points.map((p) => p.value);
  return `${Math.min(...values).toFixed(digits)} – ${Math.max(...values).toFixed(digits)}`;
}

/** One line for a finished (or running) import, e.g. "12 imported, 3 already imported, 1 failed". */
export function jobSummary(job: ImportJob): string {
  const parts = [`${job.created} imported`];
  if (job.health_days) parts.push(`${job.health_days} health ${job.health_days === 1 ? 'day' : 'days'}`);
  if (job.duplicates) parts.push(`${job.duplicates} already imported`);
  if (job.outside_range) parts.push(`${job.outside_range} outside the range`);
  if (job.not_activity) parts.push(`${job.not_activity} not activities`);
  if (job.failed) parts.push(`${job.failed} failed`);
  return parts.join(', ');
}
