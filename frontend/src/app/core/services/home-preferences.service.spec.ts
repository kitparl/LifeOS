import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HomePreferencesService } from './home-preferences.service';
import { environment } from '../../../environments/environment';

describe('HomePreferencesService', () => {
  let service: HomePreferencesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HomePreferencesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('defaults to the analytics home module', () => {
    expect(service.moduleId()).toBe('analytics');
    expect(service.homeRoute()).toBe('/analytics/dashboard');
  });

  it('loads module id from API on init', () => {
    service.init();

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    expect(req.request.method).toBe('GET');
    req.flush({ key: 'home', value: { moduleId: 'tasks' } });

    expect(service.moduleId()).toBe('tasks');
    expect(service.homeRoute()).toBe('/tasks');
  });

  it('falls back to analytics for an unknown or unavailable module', () => {
    service.init();

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    req.flush({ key: 'home', value: { moduleId: 'mood' } });

    expect(service.moduleId()).toBe('analytics');
    expect(service.homeRoute()).toBe('/analytics/dashboard');
  });

  it('keeps the local seed when the API has no preference', () => {
    localStorage.setItem('lifeos-home-prefs', JSON.stringify({ moduleId: 'finance' }));
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HomePreferencesService);
    httpMock = TestBed.inject(HttpTestingController);

    expect(service.moduleId()).toBe('finance');

    service.init();
    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    req.flush({ key: 'home', value: null });

    expect(service.moduleId()).toBe('finance');
  });

  it('saves the selection and persists it in localStorage', () => {
    service.setModuleId('journal');
    expect(service.moduleId()).toBe('journal');
    expect(service.homeRoute()).toBe('/journal');

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ value: { moduleId: 'journal' } });
    req.flush({ key: 'home', value: { moduleId: 'journal' } });

    const cached = JSON.parse(localStorage.getItem('lifeos-home-prefs') || '{}');
    expect(cached.moduleId).toBe('journal');
  });

  it('ignores selecting an unavailable module and keeps the default', () => {
    service.setModuleId('does-not-exist');
    expect(service.moduleId()).toBe('analytics');

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    expect(req.request.body).toEqual({ value: { moduleId: 'analytics' } });
    req.flush({ key: 'home', value: { moduleId: 'analytics' } });
  });
});
