/**
 * Extracts the wall-clock "YYYY-MM-DDTHH:mm:ss" prefix from a pasted date/time string, ignoring
 * any trailing timezone designator (Z, +05:30, etc.) — timezone is chosen separately via the
 * tool's own from/to zone selectors, so any zone info embedded in the pasted text is intentionally
 * dropped rather than double-applied.
 */
export function extractWallClockParts(raw: string): string {
  const match = raw.trim().match(/(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(:\d{2})?/);
  if (!match) {
    throw new Error('Could not parse that date/time — try a format like 2026-01-15 14:30.');
  }
  return `${match[1]}T${match[2]}${match[3] ?? ':00'}`;
}
