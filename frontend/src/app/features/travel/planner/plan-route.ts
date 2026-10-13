import { DayRoute, PlanDay, PlanDocument, RouteMode } from '../models/share.models';
import { haversineM } from '../utils/geo';

/**
 * Distances and times of a plan, the way the PDF guide counts them (`backend export_plan.py`):
 * each stop with a place is reached from the previous place of the trip (a day starts where the
 * last one ended), back-to-back stops at one place are one point, and a day's road route counts
 * only while its points still match the day. Everything else is a straight-line estimate.
 */

export type Point = [number, number];

/** One Google route: origin + destination + 25 intermediates (backend `MAX_ROUTE_POINTS`). */
export const MAX_ROUTE_POINTS = 27;
const SAME_POINT_DEG = 1e-7;

/** How a stop is reached from the previous place of the trip. */
export interface StopLeg {
  fromName: string;
  meters: number;
  seconds: number | null;
  /** A straight-line estimate (the road is longer). */
  approx: boolean;
}

export interface DayFacts {
  /** The points the day's legs run through; empty when the day has no leg. */
  chain: Point[];
  /** The leg that reaches each stop, by stop id. */
  legs: Record<string, StopLeg>;
  meters: number;
  /** Time on the road; only when every leg of the day has one. */
  seconds: number | null;
  approx: boolean;
  /** The day has a current road route. */
  road: boolean;
  mode: RouteMode;
  /** Stops with a place. */
  places: number;
  stays: string[];
  /** Road km can be asked for: the day has legs, no current route, and fits one Google route. */
  canRoute: boolean;
}

export interface PlanFacts {
  days: DayFacts[];
  meters: number;
  seconds: number | null;
  approx: boolean;
  places: number;
}

function samePoints(a: readonly Point[], b: readonly Point[]): boolean {
  return a.length === b.length && a.every((p, i) => Math.abs(p[0] - b[i][0]) <= SAME_POINT_DEG && Math.abs(p[1] - b[i][1]) <= SAME_POINT_DEG);
}

function currentRoute(day: PlanDay, chain: readonly Point[]): DayRoute | null {
  const route = day.route;
  return route && chain.length >= 2 && route.legs.length === chain.length - 1 && samePoints(route.points, chain) ? route : null;
}

function timeOf(legs: readonly StopLeg[]): number | null {
  return legs.length && legs.every((l) => l.seconds !== null) ? legs.reduce((sum, l) => sum + (l.seconds ?? 0), 0) : null;
}

export function planFacts(doc: PlanDocument): PlanFacts {
  let last: { key: string; point: Point; name: string } | null = null;
  const days = doc.days.map((day): DayFacts => {
    const chain: Point[] = [];
    const reached: { id: string; from: string }[] = [];
    for (const stop of day.stops) {
      const place = stop.place;
      if (!place) continue;
      const key = `${place.google_place_id ?? ''}|${place.lat}|${place.lng}`;
      const point: Point = [place.lat, place.lng];
      if (last && key !== last.key) {
        if (!chain.length) chain.push(last.point);
        chain.push(point);
        reached.push({ id: stop.id, from: last.name });
      }
      last = { key, point, name: place.name };
    }
    const route = currentRoute(day, chain);
    const legs: Record<string, StopLeg> = {};
    reached.forEach(({ id, from }, i) => {
      const road = route?.legs[i];
      legs[id] = road
        ? { fromName: from, meters: road.distance_m, seconds: road.duration_s, approx: false }
        : { fromName: from, meters: haversineM(chain[i], chain[i + 1]), seconds: null, approx: true };
    });
    const all = Object.values(legs);
    return {
      chain,
      legs,
      meters: all.reduce((sum, l) => sum + l.meters, 0),
      seconds: timeOf(all),
      approx: all.some((l) => l.approx),
      road: !!route,
      mode: route?.mode ?? 'driving',
      places: day.stops.filter((s) => s.place).length,
      stays: [...new Set(day.stops.flatMap((s) => (s.stay ? [s.stay] : [])))],
      canRoute: !route && chain.length >= 2 && chain.length <= MAX_ROUTE_POINTS,
    };
  });
  const legs = days.flatMap((d) => Object.values(d.legs));
  return {
    days,
    meters: legs.reduce((sum, l) => sum + l.meters, 0),
    seconds: timeOf(legs),
    approx: legs.some((l) => l.approx),
    places: days.reduce((n, d) => n + d.places, 0),
  };
}
