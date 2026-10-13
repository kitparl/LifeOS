import { PlanDocument, PlanStop } from '../models/share.models';
import { newStop, setDayRoute, updateStop } from './plan-ops';
import { planFacts } from './plan-route';

const MANALI = { name: 'Manali', lat: 32.2432, lng: 77.1892 };
const HAMPTA = { name: 'Hampta Pass', lat: 32.2667, lng: 77.3667 };
const CHANDRATAL = { name: 'Chandratal', lat: 32.4753, lng: 77.6178 };

function stop(title: string, place: typeof MANALI | null, extra: Partial<PlanStop> = {}): PlanStop {
  return newStop({ title, place, ...extra });
}

function plan(): PlanDocument {
  return {
    schema_version: 1,
    days: [
      { title: null, notes: null, stops: [stop('Manali', MANALI), stop('Lunch', MANALI, { stay: 'Hotel Snow' }), stop('Note', null), stop('Hampta', HAMPTA)] },
      { title: null, notes: null, stops: [] },
      { title: null, notes: null, stops: [stop('Chandratal', CHANDRATAL, { stay: 'Camp' })] },
    ],
  };
}

describe('planFacts', () => {
  it('reaches each new place from the last one, and a day starts where the trip was', () => {
    const doc = plan();
    const facts = planFacts(doc);
    const [day1, day2, day3] = facts.days;
    expect(day1.chain).toEqual([[MANALI.lat, MANALI.lng], [HAMPTA.lat, HAMPTA.lng]]);
    expect(Object.keys(day1.legs)).toEqual([doc.days[0].stops[3].id]); // back-to-back Manali is one point
    expect(day1.legs[doc.days[0].stops[3].id].fromName).toBe('Manali');
    expect(day2.chain).toEqual([]);
    expect(day3.chain[0]).toEqual([HAMPTA.lat, HAMPTA.lng]);
    expect(day3.legs[doc.days[2].stops[0].id].fromName).toBe('Hampta Pass');
    expect(day1.stays).toEqual(['Hotel Snow']);
    expect(day1.places).toBe(3);
  });

  it('uses straight-line estimates until a day has a road route, then road km and time', () => {
    const before = planFacts(plan());
    expect(before.days[0].approx).toBeTrue();
    expect(before.days[0].meters).toBeGreaterThan(16_000);
    expect(before.days[0].meters).toBeLessThan(18_000);
    expect(before.days[0].seconds).toBeNull();
    expect(before.days[0].canRoute).toBeTrue();

    const doc = setDayRoute(plan(), 0, {
      mode: 'driving',
      points: before.days[0].chain,
      legs: [{ distance_m: 51_000, duration_s: 3_100, polyline: '' }],
    });
    const after = planFacts(doc);
    expect(after.days[0]).toEqual(jasmine.objectContaining({ meters: 51_000, seconds: 3_100, approx: false, road: true, canRoute: false }));
    expect(after.days[2].approx).toBeTrue(); // day 3 still an estimate
    expect(after.meters).toBeCloseTo(51_000 + after.days[2].meters, 3);
    expect(after.seconds).toBeNull(); // not every leg has a time
  });

  it('drops a road route as soon as the day changes', () => {
    const base = plan();
    const chain = planFacts(base).days[0].chain;
    const routed = setDayRoute(base, 0, { mode: 'driving', points: chain, legs: [{ distance_m: 51_000, duration_s: 3_100, polyline: '' }] });
    const moved = updateStop(routed, 0, routed.days[0].stops[3].id, { place: CHANDRATAL });
    const facts = planFacts(moved).days[0];
    expect(facts.road).toBeFalse();
    expect(facts.approx).toBeTrue();
    expect(facts.canRoute).toBeTrue();
  });

  it('cannot ask for road km on a day longer than one Google route', () => {
    const stops = Array.from({ length: 28 }, (_, i) => stop(`S${i}`, { name: `P${i}`, lat: 30 + i / 10, lng: 77 }));
    const facts = planFacts({ schema_version: 1, days: [{ title: null, notes: null, stops }] });
    expect(facts.days[0].chain.length).toBe(28);
    expect(facts.days[0].canRoute).toBeFalse();
  });
});
