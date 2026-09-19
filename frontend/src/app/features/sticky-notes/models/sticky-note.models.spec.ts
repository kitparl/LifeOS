import {
  STICKY_NOTES_PURGE_AFTER_DAYS,
  currentMonthKey,
  daysUntilPurge,
  stickyNoteDisplayTitle,
  stickyNoteMonthKey,
  stickyNoteMonthLabel,
  stickyNoteYearOptions,
} from './sticky-note.models';

describe('sticky-note.models', () => {
  describe('stickyNoteDisplayTitle', () => {
    it('prefers the explicit title', () => {
      expect(stickyNoteDisplayTitle({ title: 'Groceries', content: 'eggs\nmilk' })).toBe('Groceries');
    });

    it('falls back to the first non-blank content line', () => {
      expect(stickyNoteDisplayTitle({ title: null, content: '\n  \nBuy milk\nmore text' })).toBe('Buy milk');
    });

    it('falls back to "New note" when both title and content are blank', () => {
      expect(stickyNoteDisplayTitle({ title: null, content: '' })).toBe('New note');
    });
  });

  describe('stickyNoteMonthLabel', () => {
    it('formats a YYYY-MM key as a month/year label', () => {
      expect(stickyNoteMonthLabel('2026-01')).toBe('January 2026');
    });
  });

  describe('currentMonthKey', () => {
    it('returns a YYYY-MM string', () => {
      expect(currentMonthKey()).toMatch(/^\d{4}-\d{2}$/);
    });

    it('uses the provided date', () => {
      expect(currentMonthKey(new Date(2026, 8, 20))).toBe('2026-09');
    });
  });

  describe('stickyNoteMonthKey', () => {
    it('pads single-digit months', () => {
      expect(stickyNoteMonthKey(2026, 1)).toBe('2026-01');
    });
  });

  describe('stickyNoteYearOptions', () => {
    it('includes the last 10 years, the selected year, and years with notes', () => {
      const years = stickyNoteYearOptions([{ month: '2014-03' }], 2030, new Date(2026, 8, 1));
      expect(years[0]).toBe(2030);
      expect(years).toContain(2026);
      expect(years).toContain(2016);
      expect(years).toContain(2014);
    });
  });

  describe('daysUntilPurge', () => {
    it('returns the full retention window for a note deleted just now', () => {
      expect(daysUntilPurge(new Date().toISOString())).toBe(STICKY_NOTES_PURGE_AFTER_DAYS);
    });

    it('never goes negative once the retention window has passed', () => {
      const longAgo = new Date(Date.now() - (STICKY_NOTES_PURGE_AFTER_DAYS + 5) * 24 * 60 * 60 * 1000).toISOString();
      expect(daysUntilPurge(longAgo)).toBe(0);
    });
  });
});
