import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SettingsHomeSectionComponent } from './settings-home-section.component';
import { HomePreferencesService } from '../../core/services/home-preferences.service';
import { availableHomeDestinations } from '../../shared/layout/nav-registry';
import { environment } from '../../../environments/environment';

describe('SettingsHomeSectionComponent', () => {
  let fixture: ComponentFixture<SettingsHomeSectionComponent>;
  let homePrefs: HomePreferencesService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [SettingsHomeSectionComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsHomeSectionComponent);
    homePrefs = TestBed.inject(HomePreferencesService);
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  function selectEl(): HTMLSelectElement {
    return fixture.nativeElement.querySelector('select') as HTMLSelectElement;
  }

  it('lists every module the user can open and selects the default', () => {
    const select = selectEl();
    const labels = Array.from(select.options).map((option) => option.textContent?.trim());

    expect(select.options.length).toBe(availableHomeDestinations().length);
    expect(labels).toContain('Analytics');
    expect(labels).toContain('Tasks');
    expect(labels).not.toContain('Mood');
    expect(select.value).toBe('analytics');
  });

  it('selects only one module and saves the preference', () => {
    const select = selectEl();
    select.value = 'tasks';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ value: { moduleId: 'tasks' } });
    req.flush({ key: 'home', value: { moduleId: 'tasks' } });

    expect(homePrefs.moduleId()).toBe('tasks');
    expect(selectEl().value).toBe('tasks');
  });
});
