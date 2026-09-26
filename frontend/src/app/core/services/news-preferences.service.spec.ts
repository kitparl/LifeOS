import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { NewsPreferencesService } from './news-preferences.service';
import { environment } from '../../../environments/environment';

describe('NewsPreferencesService', () => {
  const url = `${environment.apiUrl}/preferences/news`;
  let httpMock: HttpTestingController;

  const create = (): NewsPreferencesService => TestBed.inject(NewsPreferencesService);

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

  it('defaults to cards on Latest', () => {
    const service = create();
    expect(service.layout()).toBe('cards');
    expect(service.defaultView()).toBe('latest');
    expect(service.defaultCategory()).toBeNull();
  });

  it('seeds from localStorage before init', () => {
    localStorage.setItem('lifeos-news-prefs', JSON.stringify({ layout: 'list', defaultView: 'sports' }));
    const service = create();
    expect(service.layout()).toBe('list');
    expect(service.defaultCategory()).toBe('sports');
  });

  it('loads prefs from the API on init', () => {
    const service = create();
    service.init();
    httpMock.expectOne(url).flush({ key: 'news', value: { layout: 'grid', defaultView: 'ai' } });

    expect(service.layout()).toBe('grid');
    expect(service.defaultCategory()).toBe('ai');
  });

  it('falls back to defaults for invalid values', () => {
    const service = create();
    service.init();
    httpMock.expectOne(url).flush({ key: 'news', value: { layout: 'masonry', defaultView: 42 } });

    expect(service.layout()).toBe('cards');
    expect(service.defaultView()).toBe('latest');
  });

  it('saves each change and keeps the other field', () => {
    const service = create();
    service.setLayout('list');
    httpMock.expectOne(url).flush({});
    service.setDefaultView('business');
    const req = httpMock.expectOne(url);

    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ value: { layout: 'list', defaultView: 'business' } });
    expect(JSON.parse(localStorage.getItem('lifeos-news-prefs') ?? '{}')).toEqual({ layout: 'list', defaultView: 'business' });
    req.flush({});
  });
});
