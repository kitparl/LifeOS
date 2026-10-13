import { ShareText } from '../../../shared/share/share-links';
import { PlanDocument, PlanStop, VersionRow } from '../models/share.models';

/** "3 days · 12 stops · 2 added · 1 removed · 3 changed · ~412 km" (straight-line km, hence "~"). */
export function summaryLine(row: Pick<VersionRow, 'kind' | 'summary'>): string {
  const s = row.summary;
  const parts = [plural(s.days, 'day'), plural(s.stops, 'stop')];
  if (row.kind !== 'original') {
    if (s.added) parts.push(`${s.added} added`);
    if (s.removed) parts.push(`${s.removed} removed`);
    if (s.changed) parts.push(`${s.changed} changed`);
    if (!s.added && !s.removed && !s.changed) parts.push('same as Original');
  }
  if (s.km > 0) parts.push(`~${Math.round(s.km).toLocaleString()} km`);
  return parts.join(' · ');
}

export type StatusBadge = 'Original' | 'Draft' | 'Sent' | 'Final plan' | 'Backup' | 'Yours';

/** The badge text for a version row; colour is never the only signal (WCAG 1.4.1). */
export function statusBadge(row: Pick<VersionRow, 'kind' | 'status' | 'is_locked'>): StatusBadge {
  if (row.is_locked) return 'Final plan';
  if (row.kind === 'original') return 'Original';
  if (row.kind === 'backup') return 'Backup';
  if (row.kind === 'owner') return 'Yours';
  return row.status === 'submitted' ? 'Sent' : 'Draft';
}

export type StopChange = 'added' | 'removed' | 'changed' | 'same';

/** Per-day comparison of a version with the Original, by stop id (same rule as the backend summary). */
export function compareDays(
  original: PlanDocument,
  version: PlanDocument,
): { day: number; stops: { stop: PlanStop; change: StopChange }[] }[] {
  const before = new Map<string, { day: number; stop: PlanStop }>();
  original.days.forEach((d, day) => d.stops.forEach((stop) => before.set(stop.id, { day, stop })));
  const after = new Set<string>();
  const days = Math.max(original.days.length, version.days.length);
  const result = Array.from({ length: days }, (_, day) => ({ day, stops: [] as { stop: PlanStop; change: StopChange }[] }));
  version.days.forEach((d, day) =>
    d.stops.forEach((stop) => {
      after.add(stop.id);
      const old = before.get(stop.id);
      const change: StopChange = !old ? 'added' : old.day !== day || !sameStop(old.stop, stop) ? 'changed' : 'same';
      result[day].stops.push({ stop, change });
    }),
  );
  before.forEach(({ day, stop }, id) => {
    if (!after.has(id)) result[day].stops.push({ stop, change: 'removed' });
  });
  return result;
}

function sameStop(a: PlanStop, b: PlanStop): boolean {
  const strip = ({ id: _id, ...rest }: PlanStop) => rest;
  return JSON.stringify(strip(a)) === JSON.stringify(strip(b));
}

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? '' : 's'}`;
}

export const TRIP_SHARE_TEXT: ShareText = {
  heading: 'Share this link with friends',
  shareLabel: 'Share link',
  qrHint: 'Friends can scan this to open the plan.',
  filePrefix: 'trip',
  subject: (name) => `Help plan ${name}`,
  message: (name, url) => `Help me plan "${name}"! Open the link, add places and send me your plan: ${url}`,
};
