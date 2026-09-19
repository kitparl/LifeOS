import { extractWallClockParts, toDatetimeLocalValue } from './datetime-parse.util';

describe('datetime-parse.util', () => {
  describe('extractWallClockParts', () => {
    it('accepts a bare "YYYY-MM-DDTHH:mm" value (adds seconds)', () => {
      expect(extractWallClockParts('2026-01-15T14:30')).toBe('2026-01-15T14:30:00');
    });

    it('accepts a value with seconds already present', () => {
      expect(extractWallClockParts('2026-01-15T14:30:45')).toBe('2026-01-15T14:30:45');
    });

    it('accepts a space separator instead of "T"', () => {
      expect(extractWallClockParts('2026-01-15 14:30')).toBe('2026-01-15T14:30:00');
    });

    it('ignores a trailing zone designator, keeping only the wall clock', () => {
      expect(extractWallClockParts('2026-01-15T14:30:00Z')).toBe('2026-01-15T14:30:00');
      expect(extractWallClockParts('2026-01-15T14:30:00+05:30')).toBe('2026-01-15T14:30:00');
    });

    it('throws a clear error for unparseable input', () => {
      expect(() => extractWallClockParts('not a date')).toThrowError(/Could not parse/);
    });
  });

  describe('toDatetimeLocalValue', () => {
    it('formats a Date as YYYY-MM-DDTHH:mm', () => {
      const d = new Date(2026, 0, 15, 9, 5);
      expect(toDatetimeLocalValue(d)).toBe('2026-01-15T09:05');
    });
  });
});
