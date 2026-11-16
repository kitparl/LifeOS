import { ActivitySeries, ImportJob } from './models/activity.models';
import { chartPoints, clockLabel, isJobActive, jobSummary, paceLabel, rangeLabel } from './activity.utils';

const series = (over: Partial<ActivitySeries> = {}): ActivitySeries => ({
  sample_count: 4,
  time_s: [0, 60, 120, 180],
  distance_m: [0, 200, 400, 600],
  heart_rate: [140, null, 150, 155],
  cadence: null,
  altitude_m: [100, 101, 102, 103],
  speed_mps: [3.3333, 0.2, 3.3333, 3.3333],
  route: [],
  ...over,
});

const job = (over: Partial<ImportJob> = {}): ImportJob => ({
  id: 'j1',
  status: 'finished',
  range_mode: '12m',
  files_found: 5,
  created: 3,
  duplicates: 0,
  outside_range: 0,
  not_activity: 0,
  failed: 0,
  runs_created: 3,
  runs_matched: 0,
  errors: [],
  error: null,
  created_at: '2026-11-16T10:00:00Z',
  started_at: null,
  finished_at: null,
  ...over,
});

describe('activity utils', () => {
  it('labels pace and clock values and shows a dash for unknowns', () => {
    expect(paceLabel(306)).toBe('5:06 /km');
    expect(paceLabel(null)).toBe('—');
    expect(paceLabel(0)).toBe('—');
    expect(clockLabel(3121)).toBe('52:01');
    expect(clockLabel(3725)).toBe('1:02:05');
    expect(clockLabel(undefined)).toBe('—');
  });

  it('knows which import states are still in progress', () => {
    expect(isJobActive(job({ status: 'queued' }))).toBeTrue();
    expect(isJobActive(job({ status: 'running' }))).toBeTrue();
    expect(isJobActive(job({ status: 'finished' }))).toBeFalse();
    expect(isJobActive(job({ status: 'interrupted' }))).toBeFalse();
    expect(isJobActive(null)).toBeFalse();
  });

  it('summarises an import and leaves out zero counts except imported', () => {
    expect(jobSummary(job())).toBe('3 imported');
    expect(jobSummary(job({ created: 0, duplicates: 2, outside_range: 1, not_activity: 4, failed: 1 }))).toBe(
      '0 imported, 2 already imported, 1 outside the range, 4 not activities, 1 failed',
    );
  });

  it('plots a channel against distance and skips samples without a value', () => {
    const points = chartPoints(series(), 'heart_rate');
    expect(points).toEqual([
      { label: '0.00', value: 140 },
      { label: '0.40', value: 150 },
      { label: '0.60', value: 155 },
    ]);
  });

  it('derives pace in minutes per km from speed and skips samples where the runner stood still', () => {
    const points = chartPoints(series(), 'pace');
    expect(points.length).toBe(3);
    expect(points[0].value).toBeCloseTo(5.0, 2);
  });

  it('falls back to elapsed minutes without a distance channel and returns nothing for a missing channel', () => {
    const indoor = series({ distance_m: null });
    expect(chartPoints(indoor, 'altitude_m')[1].label).toBe('1.0');
    expect(chartPoints(series(), 'cadence')).toEqual([]);
  });

  it('describes the range of a chart', () => {
    expect(rangeLabel([])).toBe('');
    expect(rangeLabel([{ label: 'a', value: 140 }, { label: 'b', value: 155 }])).toBe('140 – 155');
  });
});
