import { ActivityDetail } from '../models/activity.models';
import { buildStats } from './activity-sections.component';

const base: ActivityDetail = {
  id: 'a1',
  source: 'garmin',
  sport: 'running',
  start_time_utc: '2026-05-03T01:00:00Z',
  timezone: 'Asia/Kolkata',
  elapsed_seconds: 3181,
  timer_seconds: 3121,
  distance_m: 10200,
  elevation_gain_m: 25,
  avg_hr: 150,
  max_hr: 171,
  avg_cadence: 170,
  max_speed_mps: null,
  calories: 700,
  device: 'Garmin fr255 music',
  training_effect_aerobic: 3.4,
  training_effect_anaerobic: 0.8,
  laps: [],
  splits: [],
  has_route: true,
  has_series: true,
  has_original_file: true,
};

describe('buildStats', () => {
  it('lists the recorded numbers of a run', () => {
    const stats = Object.fromEntries(buildStats(base).map((s) => [s.label, s.value]));

    expect(stats['Distance']).toBe('10.20 km');
    expect(stats['Moving time']).toBe('52:01');
    expect(stats['Elapsed time']).toBe('53:01');
    expect(stats['Average pace']).toBe('5:06 /km');
    expect(stats['Heart rate']).toBe('150 avg · 171 max bpm');
    expect(stats['Cadence']).toBe('170 spm');
    expect(stats['Training effect']).toBe('3.4 aerobic · 0.8 anaerobic');
    expect(stats['Device']).toBe('Garmin fr255 music');
  });

  it('leaves out what the watch did not record instead of showing zero', () => {
    const labels = buildStats({
      ...base,
      elevation_gain_m: null,
      avg_hr: null,
      max_hr: null,
      avg_cadence: null,
      calories: null,
      device: null,
      training_effect_aerobic: null,
      training_effect_anaerobic: null,
      elapsed_seconds: base.timer_seconds,
    }).map((s) => s.label);

    expect(labels).toEqual(['Distance', 'Moving time', 'Average pace']);
  });

  it('uses rpm for cadence outside running', () => {
    const cadence = buildStats({ ...base, sport: 'cycling', avg_cadence: 85 }).find((s) => s.label === 'Cadence');
    expect(cadence?.value).toBe('85 rpm');
  });
});
