import { PlanDocument, PlanStop, VersionRow } from '../models/share.models';
import { compareDays, statusBadge, summaryLine } from './plan-summary';

const stop = (id: string, title: string, extra: Partial<PlanStop> = {}): PlanStop => ({
  id,
  title,
  kind: 'other',
  place: null,
  start_time: null,
  end_time: null,
  transport: null,
  stay: null,
  notes: null,
  links: [],
  ...extra,
});
const doc = (...days: PlanStop[][]): PlanDocument => ({
  schema_version: 1,
  days: days.map((stops) => ({ title: null, notes: null, stops })),
});

describe('plan summary', () => {
  const summary = { days: 3, stops: 7, added: 2, removed: 1, changed: 0, km: 411.6 };

  it('describes a version in plain words, with straight-line km marked approximate', () => {
    expect(summaryLine({ kind: 'plan', summary })).toBe('3 days · 7 stops · 2 added · 1 removed · ~412 km');
    expect(summaryLine({ kind: 'original', summary: { ...summary, km: 0 } })).toBe('3 days · 7 stops');
    expect(summaryLine({ kind: 'plan', summary: { ...summary, added: 0, removed: 0, km: 0, days: 1, stops: 1 } })).toBe(
      '1 day · 1 stop · same as Original',
    );
  });

  it('labels every status in words (never colour alone)', () => {
    const row = (kind: VersionRow['kind'], status: VersionRow['status'], is_locked = false) => ({ kind, status, is_locked });
    expect(statusBadge(row('plan', 'submitted', true))).toBe('Final plan');
    expect(statusBadge(row('original', 'draft'))).toBe('Original');
    expect(statusBadge(row('plan', 'submitted'))).toBe('Sent');
    expect(statusBadge(row('plan', 'draft'))).toBe('Draft');
    expect(statusBadge(row('backup', 'draft'))).toBe('Backup');
    expect(statusBadge(row('owner', 'draft'))).toBe('Yours');
  });

  it('compares a version with the Original per day by stop id', () => {
    const original = doc([stop('a', 'Manali'), stop('b', 'Hampta')], [stop('c', 'Chandratal')]);
    const version = doc([stop('a', 'Manali'), stop('n', 'Cafe')], [stop('b', 'Hampta')]);
    const days = compareDays(original, version);
    expect(days[0].stops.map((s) => [s.stop.title, s.change])).toEqual([
      ['Manali', 'same'],
      ['Cafe', 'added'],
    ]);
    expect(days[1].stops.map((s) => [s.stop.title, s.change])).toEqual([
      ['Hampta', 'changed'],
      ['Chandratal', 'removed'],
    ]);
  });
});
