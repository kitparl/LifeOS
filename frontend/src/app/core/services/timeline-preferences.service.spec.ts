import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TimelinePreferencesService } from './timeline-preferences.service';
import { environment } from '../../../environments/environment';

describe('TimelinePreferencesService', () => {
  const url = `${environment.apiUrl}/preferences/timeline`;
  let httpMock: HttpTestingController;

  const create = (): TimelinePreferencesService => TestBed.inject(TimelinePreferencesService);

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('starts with no overrides', () => {
    expect(create().overrides()).toEqual({});
  });

  it('seeds from localStorage before init', () => {
    localStorage.setItem('lifeos-timeline-prefs', JSON.stringify({ sources: { tasks: false } }));
    expect(create().overrides()).toEqual({ tasks: false });
  });

  it('loads overrides from the API and drops non-boolean values', () => {
    const service = create();
    service.init();
    httpMock.expectOne(url).flush({ key: 'timeline', value: { sources: { routines: true, tasks: 'no' } } });

    expect(service.overrides()).toEqual({ routines: true });
  });

  it('saves a toggle and keeps earlier overrides', () => {
    const service = create();
    service.setSourceEnabled('tasks', false);
    httpMock.expectOne(url).flush({});
    service.setSourceEnabled('routines', true);
    const req = httpMock.expectOne(url);

    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ value: { sources: { tasks: false, routines: true } } });
    req.flush({});
    expect(JSON.parse(localStorage.getItem('lifeos-timeline-prefs') ?? '{}')).toEqual({
      sources: { tasks: false, routines: true },
    });
  });
});
