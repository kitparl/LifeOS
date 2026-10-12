import { ItineraryDay, ItineraryItem, Stop, TripPlace } from '../models/travel.models';
import { dayEndpoints, moveItem, searchBias, stopDayLabels } from './itinerary';

function item(id: string, dayId: string): ItineraryItem {
  return {
    id,
    day_id: dayId,
    position: 0,
    place_id: null,
    title: id,
    start_time: null,
    end_time: null,
    transport: null,
    accommodation: null,
    notes: null,
    links: [],
  };
}

function day(id: string, ids: string[]): ItineraryDay {
  return { id, day_index: 0, day_date: null, title: null, notes: null, items: ids.map((i) => item(i, id)) };
}

describe('moveItem', () => {
  const days = [day('d1', ['manali', 'hampta', 'chika']), day('d2', ['chandratal'])];

  it('reorders within a day', () => {
    expect(moveItem(days, { dayId: 'd1', index: 2 }, { dayId: 'd1', index: 0 })).toEqual({
      d1: ['chika', 'manali', 'hampta'],
      d2: ['chandratal'],
    });
  });

  it('moves an item to another date', () => {
    expect(moveItem(days, { dayId: 'd1', index: 1 }, { dayId: 'd2', index: 1 })).toEqual({
      d1: ['manali', 'chika'],
      d2: ['chandratal', 'hampta'],
    });
  });

  it('never loses or duplicates items and leaves the input untouched', () => {
    const layout = moveItem(days, { dayId: 'd2', index: 0 }, { dayId: 'd1', index: 99 });
    const all = Object.values(layout).flat().sort();
    expect(all).toEqual(['chandratal', 'chika', 'hampta', 'manali']);
    expect(days[1].items.length).toBe(1);
  });

  it('ignores an out-of-range source', () => {
    expect(moveItem(days, { dayId: 'd1', index: 7 }, { dayId: 'd2', index: 0 })).toEqual({
      d1: ['manali', 'hampta', 'chika'],
      d2: ['chandratal'],
    });
  });
});

/** Items named after their place; `note` items have no place. Stops mirror the backend's `stop_sequence`. */
function placedDay(id: string, index: number, places: string[]): ItineraryDay {
  const items = places.map((p, i) => ({ ...item(`${id}-${i}`, id), place_id: p === 'note' ? null : p }));
  return { ...day(id, []), day_index: index, items };
}

function stop(place_id: string, day_id: string): Stop {
  return { place_id, day_id, name: place_id, lat: 0, lng: 0 };
}

describe('dayEndpoints', () => {
  it('picks the first and last stop with a place', () => {
    const ends = dayEndpoints(placedDay('d1', 0, ['note', 'kasol', 'tosh', 'manikaran', 'note']));
    expect([ends?.start.place_id, ends?.end.place_id]).toEqual(['kasol', 'manikaran']);
  });

  it('has no endpoints for a day with fewer than two places', () => {
    expect(dayEndpoints(placedDay('d1', 0, ['kasol', 'note']))).toBeNull();
  });
});

describe('stopDayLabels', () => {
  it('labels each day start and end, including a stop shared across days', () => {
    const days = [placedDay('d1', 0, ['manali', 'kasol']), placedDay('d2', 1, ['kasol', 'tosh', 'manikaran'])];
    const stops = [stop('manali', 'd1'), stop('kasol', 'd1'), stop('tosh', 'd2'), stop('manikaran', 'd2')];
    expect(Object.fromEntries(stopDayLabels(days, stops))).toEqual({
      0: ['Day 1 start'],
      1: ['Day 1 end', 'Day 2 start'],
      3: ['Day 2 end'],
    });
  });

  it('labels the right pin on a loop that returns to its start', () => {
    const days = [placedDay('d1', 0, ['kasol', 'tosh', 'kasol'])];
    const stops = [stop('kasol', 'd1'), stop('tosh', 'd1'), stop('kasol', 'd1')];
    expect(Object.fromEntries(stopDayLabels(days, stops))).toEqual({ 0: ['Day 1 start'], 2: ['Day 1 end'] });
  });
});

describe('searchBias', () => {
  const place = (id: string, lat: number, lng: number): TripPlace => ({ id, name: id, lat, lng, status: 'wishlist', external_place_id: null });
  const places = [place('a', 10, 20), place('b', 30, 40), place('c', 50, 60)];
  const placed = (ids: string[]): ItineraryDay => ({ ...day('d', []), items: ids.map((id) => ({ ...item(id, 'd'), place_id: id })) });

  it('centres on the day pins', () => {
    expect(searchBias(placed(['a', 'b']), places)).toEqual({ lat: 20, lng: 30 });
  });

  it('falls back to every pin on the trip when the day has none', () => {
    expect(searchBias(placed([]), places)).toEqual({ lat: 30, lng: 40 });
  });

  it('is null for a trip with no places', () => {
    expect(searchBias(placed([]), [])).toBeNull();
  });
});
