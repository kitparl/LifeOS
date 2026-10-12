import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { TripPlace } from '../models/travel.models';
import { SEARCH_DEBOUNCE_MS } from '../services/maps-api.service';
import { PickedPlace, PlaceSearchComponent } from './place-search.component';

describe('PlaceSearchComponent (inside a trip)', () => {
  let fixture: ComponentFixture<PlaceSearchComponent>;
  let component: PlaceSearchComponent;
  let http: HttpTestingController;
  const tripPlaces: TripPlace[] = [
    { id: 'p1', name: 'Manali', lat: 32.2, lng: 77.1, status: 'wishlist', external_place_id: null },
    { id: 'p2', name: 'Tosh', lat: 32, lng: 77.4, status: 'wishlist', external_place_id: null },
  ];
  const saved = (id: string, name: string) => ({ id, name, city: null, country: 'India' });

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [PlaceSearchComponent], providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(PlaceSearchComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('tripPlaces', tripPlaces);
    fixture.componentRef.setInput('includeSaved', true);
    fixture.componentRef.setInput('clearOnPick', true);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('lists trip places at once and hides trip places from the saved group', fakeAsync(() => {
    component.onQuery('ma');
    expect(component.tripMatches().map((p) => p.name)).toEqual(['Manali']);

    tick(SEARCH_DEBOUNCE_MS);
    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/travel/places`);
    expect(req.request.params.get('q')).toBe('ma');
    req.flush([saved('p1', 'Manali'), saved('p9', 'Mandi')], { headers: { 'X-Total-Count': '2' } });
    http.expectNone((r) => r.url.includes('/maps/autocomplete'));

    expect(component.savedMatches().map((p) => p.name)).toEqual(['Mandi']);
    expect(component.hasResults()).toBeTrue();
  }));

  it('emits the picked place and empties the box for the next pick', () => {
    const picked: PickedPlace[] = [];
    component.pickedPlace.subscribe((p) => picked.push(p));
    component.onQuery('tos');
    component.pickPlace(tripPlaces[1]);
    expect(picked).toEqual([{ id: 'p2', name: 'Tosh' }]);
    expect(component.query()).toBe('');
    expect(component.open()).toBeFalse();
  });
});
