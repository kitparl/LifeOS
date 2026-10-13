import { PlanDocument } from '../models/share.models';
import { addDay, addStop, moveStopToDay, newStop, nudgeStop, removeDay, removeStop, stopCount, updateStop } from './plan-ops';

const titles = (doc: PlanDocument) => doc.days.map((d) => d.stops.map((s) => s.title));

describe('plan-ops', () => {
  const a = newStop({ title: 'Manali' });
  const b = newStop({ title: 'Hampta' });
  const c = newStop({ title: 'Chandratal' });
  const doc: PlanDocument = {
    schema_version: 1,
    days: [
      { title: null, notes: null, stops: [a, b] },
      { title: null, notes: null, stops: [c] },
    ],
  };

  it('never changes the document it was given (undo keeps the old one)', () => {
    const before = JSON.stringify(doc);
    removeStop(addStop(nudgeStop(doc, 0, 0, 1), 1, newStop({ title: 'Cafe' })), 0, a.id);
    expect(JSON.stringify(doc)).toBe(before);
  });

  it('moves stops with up / down inside a day and across days', () => {
    expect(titles(nudgeStop(doc, 0, 0, 1))).toEqual([['Hampta', 'Manali'], ['Chandratal']]);
    expect(titles(nudgeStop(doc, 0, 1, 1))).toEqual([['Manali'], ['Hampta', 'Chandratal']]);
    expect(titles(nudgeStop(doc, 1, 0, -1))).toEqual([['Manali', 'Hampta', 'Chandratal'], []]);
    expect(nudgeStop(doc, 0, 0, -1)).toBe(doc); // already first of the first day
  });

  it('drags a stop to a position in another day', () => {
    expect(titles(moveStopToDay(doc, 1, 0, 0, 1))).toEqual([['Manali', 'Chandratal', 'Hampta'], []]);
  });

  it('adds, changes and removes stops and days', () => {
    let next = addDay(doc);
    next = addStop(next, 2, newStop({ title: 'Home', kind: 'travel' }));
    next = updateStop(next, 0, a.id, { title: 'Old Manali', start_time: '09:30' });
    expect(titles(next)).toEqual([['Old Manali', 'Hampta'], ['Chandratal'], ['Home']]);
    expect(next.days[0].stops[0].id).toBe(a.id);
    expect(stopCount(removeDay(next, 1))).toBe(3);
  });

  it('gives every new stop its own id', () => {
    expect(newStop({ title: 'x' }).id).not.toBe(newStop({ title: 'x' }).id);
  });
});
