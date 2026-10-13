import { DayRoute, PlanDay, PlanDocument, PlanStop } from '../models/share.models';

/** Pure, immutable edits of a plan document. Every edit returns a new document (undo keeps the old one). */

export type StopFields = Omit<PlanStop, 'id'>;

export function newStop(fields: Partial<StopFields> & Pick<StopFields, 'title'>): PlanStop {
  return {
    id: crypto.randomUUID(),
    kind: 'other',
    place: null,
    start_time: null,
    end_time: null,
    transport: null,
    stay: null,
    notes: null,
    links: [],
    ...fields,
  };
}

function withDays(doc: PlanDocument, days: PlanDay[]): PlanDocument {
  return { ...doc, days };
}

function withStops(doc: PlanDocument, day: number, stops: PlanStop[]): PlanDocument {
  return withDays(
    doc,
    doc.days.map((d, i) => (i === day ? { ...d, stops } : d)),
  );
}

function move<T>(list: readonly T[], from: number, to: number): T[] {
  const next = [...list];
  if (from < 0 || from >= next.length) return next;
  const [item] = next.splice(from, 1);
  next.splice(Math.max(0, Math.min(to, next.length)), 0, item);
  return next;
}

export function addDay(doc: PlanDocument): PlanDocument {
  return withDays(doc, [...doc.days, { title: null, notes: null, stops: [] }]);
}

export function removeDay(doc: PlanDocument, day: number): PlanDocument {
  return withDays(
    doc,
    doc.days.filter((_, i) => i !== day),
  );
}

export function moveDay(doc: PlanDocument, from: number, to: number): PlanDocument {
  return withDays(doc, move(doc.days, from, to));
}

export function addStop(doc: PlanDocument, day: number, stop: PlanStop): PlanDocument {
  return withStops(doc, day, [...doc.days[day].stops, stop]);
}

export function updateStop(doc: PlanDocument, day: number, id: string, patch: Partial<StopFields>): PlanDocument {
  return withStops(
    doc,
    day,
    doc.days[day].stops.map((s) => (s.id === id ? { ...s, ...patch } : s)),
  );
}

export function removeStop(doc: PlanDocument, day: number, id: string): PlanDocument {
  return withStops(
    doc,
    day,
    doc.days[day].stops.filter((s) => s.id !== id),
  );
}

export function moveStop(doc: PlanDocument, day: number, from: number, to: number): PlanDocument {
  return withStops(doc, day, move(doc.days[day].stops, from, to));
}

/** Moves a stop to another day at `to` (the end when omitted). */
export function moveStopToDay(doc: PlanDocument, fromDay: number, index: number, toDay: number, to?: number): PlanDocument {
  if (fromDay === toDay) return moveStop(doc, fromDay, index, to ?? doc.days[fromDay].stops.length - 1);
  const stop = doc.days[fromDay]?.stops[index];
  if (!stop) return doc;
  const removed = withStops(doc, fromDay, doc.days[fromDay].stops.filter((_, i) => i !== index));
  const target = [...removed.days[toDay].stops];
  target.splice(to ?? target.length, 0, stop);
  return withStops(removed, toDay, target);
}

/** Moving a stop with the up / down buttons: inside its day, then across to the next or previous day. */
export function nudgeStop(doc: PlanDocument, day: number, index: number, direction: -1 | 1): PlanDocument {
  const stops = doc.days[day].stops;
  const to = index + direction;
  if (to >= 0 && to < stops.length) return moveStop(doc, day, index, to);
  const otherDay = day + direction;
  if (otherDay < 0 || otherDay >= doc.days.length) return doc;
  return moveStopToDay(doc, day, index, otherDay, direction === 1 ? 0 : doc.days[otherDay].stops.length);
}

/** Road km for a day; it counts only while the day's chain stays the same (see `plan-route.ts`). */
export function setDayRoute(doc: PlanDocument, day: number, route: DayRoute): PlanDocument {
  return withDays(
    doc,
    doc.days.map((d, i) => (i === day ? { ...d, route } : d)),
  );
}

export function stopCount(doc: PlanDocument): number {
  return doc.days.reduce((n, d) => n + d.stops.length, 0);
}
