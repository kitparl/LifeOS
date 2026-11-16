import {
  buildDayPayload,
  chartSegments,
  clockToMinutes,
  cleanMessage,
  fieldText,
  formatMetric,
  manualValues,
  markerLabel,
  minutesToClock,
  sleepLabel,
} from './health.utils';
import { MetricInfo } from './models/health.models';

const metric = (over: Partial<MetricInfo>): MetricInfo => ({
  key: 'resting_hr',
  label: 'Resting heart rate',
  unit: 'bpm',
  group: 'heart',
  kind: 'int',
  min: 20,
  max: 150,
  lower_is_better: true,
  today: true,
  ...over,
});

const catalogue: MetricInfo[] = [
  metric({}),
  metric({ key: 'hrv_ms', label: 'HRV', unit: 'ms', kind: 'float' }),
  metric({ key: 'bed_time_min', label: 'Bed time', unit: '', kind: 'clock', group: 'sleep' }),
];

describe('health utils', () => {
  it('converts clock times both ways and rejects bad times', () => {
    expect(minutesToClock(1410)).toBe('23:30');
    expect(minutesToClock(5)).toBe('00:05');
    expect(clockToMinutes('23:30')).toBe(1410);
    expect(clockToMinutes('7:30')).toBeNull();
    expect(clockToMinutes('25:00')).toBeNull();
    expect(clockToMinutes('')).toBeNull();
  });

  it('formats sleep, clock and ordinary values', () => {
    expect(sleepLabel(432)).toBe('7 h 12 min');
    expect(sleepLabel(45)).toBe('45 min');
    expect(sleepLabel(null)).toBe('—');
    expect(formatMetric({ key: 'sleep_total_min', unit: 'min' }, 420)).toBe('7 h 00 min');
    expect(formatMetric({ key: 'bed_time_min', unit: '', kind: 'clock' }, 1410)).toBe('23:30');
    expect(formatMetric({ key: 'resting_hr', unit: 'bpm' }, 52)).toBe('52 bpm');
    expect(formatMetric({ key: 'hrv_ms', unit: 'ms' }, 48.46)).toBe('48.5 ms');
    expect(formatMetric({ key: 'steps', unit: '' }, undefined)).toBe('—');
  });

  it('words the comparison with the 30-day average', () => {
    expect(markerLabel('up')).toBe('above your 30-day average');
    expect(markerLabel('down')).toBe('below your 30-day average');
    expect(markerLabel('flat')).toBe('in line with your 30-day average');
    expect(markerLabel(null)).toBe('');
  });

  it('splits a series into runs so a missing day breaks the line', () => {
    const points = [
      { day: 'a', value: 1 },
      { day: 'b', value: 2 },
      { day: 'c', value: null },
      { day: 'd', value: 4 },
      { day: 'e', value: null },
      { day: 'f', value: null },
      { day: 'g', value: 7 },
      { day: 'h', value: 8 },
    ];
    expect(chartSegments(points).map((seg) => seg.map((d) => d.index))).toEqual([[0, 1], [3], [6, 7]]);
    expect(chartSegments([{ day: 'a', value: null }])).toEqual([]);
  });

  it('builds a payload of the filled fields only and converts clock fields to minutes', () => {
    const { values, invalid } = buildDayPayload({ resting_hr: '52', hrv_ms: '48,5', bed_time_min: '23:30' }, catalogue);
    expect(values).toEqual({ resting_hr: 52, hrv_ms: 48.5, bed_time_min: 1410 });
    expect(invalid).toEqual([]);
    expect(buildDayPayload({ resting_hr: '   ', hrv_ms: '' }, catalogue).values).toEqual({});
  });

  it('reports fields that are not valid numbers or times', () => {
    const { values, invalid } = buildDayPayload({ resting_hr: 'fast', bed_time_min: '9pm', hrv_ms: '40' }, catalogue);
    expect(invalid).toEqual(['Resting heart rate', 'Bed time']);
    expect(values).toEqual({ hrv_ms: 40 });
  });

  it('shows stored values as form text and tells manual values from imported ones', () => {
    expect(fieldText(catalogue[2], 1410)).toBe('23:30');
    expect(fieldText(catalogue[0], 52)).toBe('52');
    expect(fieldText(catalogue[0], undefined)).toBe('');
    const day = { day: 'd', values: { resting_hr: 50, steps: 9000 }, sources: { resting_hr: 'manual', steps: 'garmin' } };
    expect(manualValues(day)).toEqual({ resting_hr: 50 });
  });

  it('strips the validation prefix from server messages', () => {
    expect(cleanMessage('Value error, Resting heart rate must be between 20 and 150')).toBe(
      'Resting heart rate must be between 20 and 150',
    );
    expect(cleanMessage('The date is in the future')).toBe('The date is in the future');
  });
});
