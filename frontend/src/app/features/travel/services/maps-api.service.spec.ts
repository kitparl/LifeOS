import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Suggestions } from '../models/travel.models';
import { MapsApiService, SEARCH_DEBOUNCE_MS } from './maps-api.service';

describe('MapsApiService', () => {
  let service: MapsApiService;
  let http: HttpTestingController;
  const base = `${environment.apiUrl}/travel/maps`;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(MapsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('never sends short queries and debounces typing into one request', fakeAsync(() => {
    const query$ = new Subject<string>();
    const results: Suggestions[] = [];
    service.searchSuggestions(query$).subscribe((r) => results.push(r));

    query$.next('Ma');
    tick(SEARCH_DEBOUNCE_MS);
    http.expectNone((r) => r.url.startsWith(`${base}/autocomplete`));
    expect(results).toEqual([{ suggestions: [], fallback_reason: null }]);

    query$.next('Man');
    tick(100);
    query$.next('Mana');
    tick(SEARCH_DEBOUNCE_MS);
    const req = http.expectOne((r) => r.url === `${base}/autocomplete`);
    expect(req.request.params.get('q')).toBe('Mana');
    expect(req.request.params.get('session')).toBeTruthy();
    req.flush({ suggestions: [], fallback_reason: null });
  }));

  it('cancels the in-flight search when the query changes', fakeAsync(() => {
    const query$ = new Subject<string>();
    service.searchSuggestions(query$).subscribe();
    query$.next('Manali');
    tick(SEARCH_DEBOUNCE_MS);
    const first = http.expectOne((r) => r.url === `${base}/autocomplete`);
    query$.next('Manikaran');
    tick(SEARCH_DEBOUNCE_MS);
    expect(first.cancelled).toBeTrue();
    http.expectOne((r) => r.url === `${base}/autocomplete`).flush({ suggestions: [], fallback_reason: null });
  }));

  it('ends the Places session when a suggestion is picked', fakeAsync(() => {
    const query$ = new Subject<string>();
    service.searchSuggestions(query$).subscribe();
    query$.next('Manali');
    tick(SEARCH_DEBOUNCE_MS);
    const search = http.expectOne((r) => r.url === `${base}/autocomplete`);
    const session = search.request.params.get('session');
    search.flush({ suggestions: [], fallback_reason: null });

    service.placeDetails('ChIJ/x').subscribe();
    const details = http.expectOne((r) => r.url === `${base}/place/ChIJ%2Fx`);
    expect(details.request.params.get('session')).toBe(session);
    details.flush({ result: null, fallback_reason: 'missing_credential' });

    query$.next('Kasol');
    tick(SEARCH_DEBOUNCE_MS);
    const next = http.expectOne((r) => r.url === `${base}/autocomplete`);
    expect(next.request.params.get('session')).not.toBe(session);
    next.flush({ suggestions: [], fallback_reason: null });
  }));
});
