import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { defaultHomeRedirect } from './default-home.guard';
import { HomePreferencesService } from '../services/home-preferences.service';
import { environment } from '../../../environments/environment';

@Component({ standalone: true, template: '' })
class BlankComponent {}

describe('defaultHomeRedirect', () => {
  let router: Router;
  let homePrefs: HomePreferencesService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([
          { path: '', pathMatch: 'full', redirectTo: defaultHomeRedirect },
          { path: 'tasks', component: BlankComponent },
          { path: 'journal', component: BlankComponent },
          { path: 'analytics/dashboard', component: BlankComponent },
        ]),
      ],
    });

    router = TestBed.inject(Router);
    homePrefs = TestBed.inject(HomePreferencesService);
    httpMock = TestBed.inject(HttpTestingController);
    await router.navigateByUrl('/analytics/dashboard');
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('redirects / to analytics when no preference is set', async () => {
    await router.navigateByUrl('/');
    expect(router.url).toBe('/analytics/dashboard');
  });

  it('redirects / to the selected module', async () => {
    homePrefs.setModuleId('tasks');
    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    req.flush({ key: 'home', value: { moduleId: 'tasks' } });

    await router.navigateByUrl('/');
    expect(router.url).toBe('/tasks');
  });

  it('falls back to analytics when the stored module is unavailable', async () => {
    localStorage.setItem('lifeos-home-prefs', JSON.stringify({ moduleId: 'mood' }));
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([
          { path: '', pathMatch: 'full', redirectTo: defaultHomeRedirect },
          { path: 'analytics/dashboard', component: BlankComponent },
        ]),
      ],
    });

    router = TestBed.inject(Router);
    httpMock = TestBed.inject(HttpTestingController);

    await router.navigateByUrl('/');
    expect(router.url).toBe('/analytics/dashboard');
  });
});
