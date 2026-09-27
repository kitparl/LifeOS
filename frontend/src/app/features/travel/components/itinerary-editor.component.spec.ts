import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ItineraryDay } from '../models/travel.models';
import { ItineraryEditorComponent, NewItem } from './itinerary-editor.component';

describe('ItineraryEditorComponent', () => {
  let fixture: ComponentFixture<ItineraryEditorComponent>;
  let component: ItineraryEditorComponent;
  const days: ItineraryDay[] = [
    {
      id: 'd1',
      day_index: 0,
      day_date: '2027-06-16',
      title: null,
      notes: null,
      items: [
        { id: 'a', day_id: 'd1', position: 0, place_id: 'p1', title: 'Manali', start_time: '08:00:00', end_time: null, transport: null, accommodation: null, notes: null, links: [] },
        { id: 'b', day_id: 'd1', position: 1, place_id: null, title: 'Drive to Jobra', start_time: null, end_time: null, transport: null, accommodation: null, notes: null, links: [] },
      ],
    },
    { id: 'd2', day_index: 1, day_date: '2027-06-17', title: null, notes: null, items: [] },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ItineraryEditorComponent] });
    fixture = TestBed.createComponent(ItineraryEditorComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('days', days);
    fixture.componentRef.setInput('places', [{ id: 'p1', name: 'Manali', lat: 32.2, lng: 77.1, status: 'wishlist', external_place_id: null }]);
    fixture.detectChanges();
  });

  it('renders days with times and places', () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Day 1');
    expect(text).toContain('08:00');
    expect(text).toContain('📍 Manali');
  });

  it('emits the whole layout once when an item moves to another day', () => {
    const layouts: Record<string, string[]>[] = [];
    component.reorder.subscribe((l) => layouts.push(l));
    component.moveTo(days[0].items[1], 'd1', 'd2');
    expect(layouts).toEqual([{ d1: ['a'], d2: ['b'] }]);
  });

  it('adds a stop named after the chosen place when no title is typed', () => {
    const added: NewItem[] = [];
    component.addItem.subscribe((i) => added.push(i));
    component.draftPlaces['d2'] = 'p1';
    component.add('d2');
    expect(added).toEqual([{ day_id: 'd2', title: 'Manali', place_id: 'p1' }]);
  });

  it('refuses to blank a stop title', () => {
    let emitted = 0;
    component.itemPatch.subscribe(() => emitted++);
    component.patch(days[0].items[0], { title: '' });
    expect(emitted).toBe(0);
  });
});
