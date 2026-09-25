import { expiresSoon, expiryLabel, relativeTime, savedAgoLabel } from './news-dates';

describe('news-dates', () => {
  // Local noon, so calendar-day math is stable in any timezone.
  const now = new Date(2026, 8, 25, 12, 0, 0);
  const at = (days: number, hours = 0, minutes = 0) =>
    new Date(now.getTime() + ((days * 24 + hours) * 60 + minutes) * 60_000).toISOString();

  describe('relativeTime', () => {
    it('formats recent, same-day, yesterday and older dates', () => {
      expect(relativeTime(at(0, 0, 0), now)).toBe('Just now');
      expect(relativeTime(at(0, 0, -2), now)).toBe('2 minutes ago');
      expect(relativeTime(at(0, -1), now)).toBe('1 hour ago');
      expect(relativeTime(at(-1), now)).toBe('Yesterday');
      expect(relativeTime(new Date(2026, 8, 1, 12).toISOString(), now)).toContain('2026');
    });

    it('returns null for missing or invalid dates', () => {
      expect(relativeTime(null, now)).toBeNull();
      expect(relativeTime('not a date', now)).toBeNull();
    });
  });

  describe('expiryLabel', () => {
    it('counts local calendar days', () => {
      expect(expiryLabel(at(29), now)).toBe('Expires in 29 days');
      expect(expiryLabel(at(2), now)).toBe('Expires in 2 days');
      expect(expiryLabel(at(1), now)).toBe('Expires tomorrow');
      expect(expiryLabel(at(0, 6), now)).toBe('Expires today');
    });

    it('never shows negative values', () => {
      expect(expiryLabel(at(-3), now)).toBe('Expires today');
    });
  });

  it('savedAgoLabel', () => {
    expect(savedAgoLabel(at(0, -1), now)).toBe('Saved today');
    expect(savedAgoLabel(at(-1), now)).toBe('Saved yesterday');
    expect(savedAgoLabel(at(-5), now)).toBe('Saved 5 days ago');
  });

  it('expiresSoon', () => {
    expect(expiresSoon(at(3), now)).toBeTrue();
    expect(expiresSoon(at(4), now)).toBeFalse();
  });
});
