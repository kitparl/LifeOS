import { ItineraryDay, ItineraryItem } from '../models/travel.models';
import { moveItem } from './itinerary';

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
