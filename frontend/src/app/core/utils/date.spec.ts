import { localIsoDate, pad2, toDatetimeLocalValue, utcIsoDate, utcIsoMinute, yearMonthKey } from './date';

describe('date utils', () => {
  it('pads to two digits', () => {
    expect(pad2(3)).toBe('03');
    expect(pad2(12)).toBe('12');
  });

  it('formats the local calendar date for date inputs', () => {
    expect(localIsoDate(new Date(2026, 7, 22))).toBe('2026-08-22');
  });

  it('formats a Date as YYYY-MM-DDTHH:mm for datetime-local inputs', () => {
    expect(toDatetimeLocalValue(new Date(2026, 0, 15, 9, 5))).toBe('2026-01-15T09:05');
  });

  it('reads the UTC calendar for utc helpers', () => {
    const d = new Date(Date.UTC(2026, 2, 4, 23, 45));
    expect(utcIsoDate(d)).toBe('2026-03-04');
    expect(utcIsoMinute(d)).toBe('2026-03-04T23:45');
  });

  it('pads single-digit months in year-month keys', () => {
    expect(yearMonthKey(2026, 1)).toBe('2026-01');
  });
});
