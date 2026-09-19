import { MONTH_NAMES, MONTH_OPTIONS } from './months';

describe('MONTH_OPTIONS', () => {
  it('covers January through December as 1–12', () => {
    expect(MONTH_OPTIONS.length).toBe(12);
    expect(MONTH_OPTIONS[0]).toEqual({ value: 1, label: 'January' });
    expect(MONTH_OPTIONS[11]).toEqual({ value: 12, label: 'December' });
    expect(MONTH_OPTIONS.map((o) => o.label)).toEqual([...MONTH_NAMES]);
  });
});
