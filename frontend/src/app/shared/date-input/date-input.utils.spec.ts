import { dateToValue, displayDate, outOfRange, parseTyped, stepDate, valueToDate } from './date-input.utils';

describe('date-input utils', () => {
  // Friday 13 Nov 2026, 14:20 local.
  const now = new Date(2026, 10, 13, 14, 20);
  const value = (text: string, mode: Parameters<typeof parseTyped>[1], current: Date | null = null) => {
    const date = parseTyped(text, mode, current, now);
    return date ? dateToValue(date, mode) : null;
  };

  it('round-trips the stored formats the native inputs used', () => {
    expect(dateToValue(valueToDate('2026-03-05', 'date')!, 'date')).toBe('2026-03-05');
    expect(dateToValue(valueToDate('2026-03-05T07:45', 'datetime')!, 'datetime')).toBe('2026-03-05T07:45');
    expect(dateToValue(valueToDate('07:45:00', 'time', now)!, 'time')).toBe('07:45');
    expect(dateToValue(valueToDate('2026-03', 'month')!, 'month')).toBe('2026-03');
    expect(valueToDate('', 'date')).toBeNull();
    expect(valueToDate('nonsense', 'time')).toBeNull();
  });

  it('reads shortcuts and plain English, day-first', () => {
    expect(value('t', 'date')).toBe('2026-11-13');
    expect(value('tm', 'date')).toBe('2026-11-14');
    expect(value('y', 'date')).toBe('2026-11-12');
    expect(value('tomorrow', 'date')).toBe('2026-11-14');
    expect(value('25 dec', 'date')).toBe('2026-12-25');
    expect(value('3/4/2026', 'date')).toBe('2026-04-03');
    expect(value('2026-01-31', 'date')).toBe('2026-01-31');
    expect(value('banana', 'date')).toBeNull();
  });

  it('gives datetimes the typed time, else the current time of day, else 9:00', () => {
    expect(value('tomorrow 5pm', 'datetime')).toBe('2026-11-14T17:00');
    expect(value('tomorrow', 'datetime')).toBe('2026-11-14T09:00');
    expect(value('tomorrow', 'datetime', new Date(2026, 0, 1, 18, 30))).toBe('2026-11-14T18:30');
    expect(value('5:30pm', 'time')).toBe('17:30');
    expect(value('09:05', 'time')).toBe('09:05');
    expect(value('march 2027', 'month')).toBe('2027-03');
  });

  it('re-reads its own display text', () => {
    for (const mode of ['date', 'datetime', 'time', 'month'] as const) {
      const shown = displayDate(new Date(2026, 1, 9, 18, 5), mode);
      expect(value(shown, mode)).withContext(`${mode}: ${shown}`).toBe(dateToValue(new Date(2026, 1, 9, 18, 5), mode));
    }
  });

  it('nudges by day / month, 15 min / hour, and clamps month ends', () => {
    expect(dateToValue(stepDate(new Date(2026, 0, 31), 'date', 'small', 1), 'date')).toBe('2026-02-01');
    expect(dateToValue(stepDate(new Date(2026, 0, 31), 'date', 'large', 1), 'date')).toBe('2026-02-28');
    expect(dateToValue(stepDate(new Date(2026, 0, 1, 9, 0), 'time', 'small', -1), 'time')).toBe('08:45');
    expect(dateToValue(stepDate(new Date(2026, 0, 1), 'month', 'large', 1), 'month')).toBe('2027-01');
  });

  it('checks min / max at the mode precision', () => {
    expect(outOfRange(new Date(2026, 10, 12), 'date', '2026-11-13', '')).toBeTrue();
    expect(outOfRange(new Date(2026, 10, 13, 23, 0), 'date', '2026-11-13', '2026-11-13')).toBeFalse();
    expect(outOfRange(new Date(2026, 11, 1), 'month', '', '2026-11')).toBeTrue();
  });
});
