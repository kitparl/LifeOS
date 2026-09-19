import { ALL_MONTHS, lastDayOfMonthIso, periodFromYearMonth } from './period';

describe('periodFromYearMonth', () => {
  const now = new Date(2026, 8, 19);

  it('defaults the current month to this_month', () => {
    expect(periodFromYearMonth(2026, 9, now)).toEqual({ preset: 'this_month' });
  });

  it('maps all months of the current year to this_year', () => {
    expect(periodFromYearMonth(2026, ALL_MONTHS, now)).toEqual({ preset: 'this_year' });
  });

  it('maps a past month to an inclusive custom range', () => {
    expect(periodFromYearMonth(2025, 2, now)).toEqual({
      preset: 'custom',
      start: '2025-02-01',
      end: '2025-02-28',
    });
  });

  it('maps all months of a past year to that calendar year', () => {
    expect(periodFromYearMonth(2024, ALL_MONTHS, now)).toEqual({
      preset: 'custom',
      start: '2024-01-01',
      end: '2024-12-31',
    });
  });
});

describe('lastDayOfMonthIso', () => {
  it('uses the last calendar day, including leap days', () => {
    expect(lastDayOfMonthIso(2024, 2)).toBe('2024-02-29');
    expect(lastDayOfMonthIso(2026, 9)).toBe('2026-09-30');
  });
});
