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

  function trigger(): HTMLButtonElement {
    return fixture.nativeElement.querySelector('#default-home-module') as HTMLButtonElement;
  }

  function openMenu(): void {
    trigger().click();
    fixture.detectChanges();
  }

  it('lists every module the user can open and selects the default', () => {
    expect(trigger().textContent).toContain('Tasks');

    openMenu();

    const options = Array.from(
      fixture.nativeElement.querySelectorAll('[role="option"]') as NodeListOf<HTMLButtonElement>,
    );
    const labels = options.map((option) => option.textContent?.trim());

    expect(options.length).toBe(availableHomeDestinations().length);
    expect(labels).toContain('Analytics');
    expect(labels).toContain('Tasks');
    expect(labels).not.toContain('Mood');
    expect(options.find((option) => option.textContent?.trim() === 'Tasks')?.classList.contains('active')).toBe(true);
  });

  it('keeps the option list scrollable when open', () => {
    openMenu();

    const options = fixture.nativeElement.querySelector('.home-module-select__options') as HTMLElement;
    expect(options).toBeTruthy();
    expect(getComputedStyle(options).overflowY).toBe('auto');
  });

  it('filters modules as the user types in search', () => {
    openMenu();

    const search = fixture.nativeElement.querySelector('input[type="search"]') as HTMLInputElement;
    expect(search).toBeTruthy();

    search.value = 'task';
    search.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const labels = Array.from(
      fixture.nativeElement.querySelectorAll('[role="option"]') as NodeListOf<HTMLButtonElement>,
    ).map((option) => option.textContent?.trim());

    expect(labels).toEqual(['Tasks']);
  });

  it('selects only one module and saves the preference', () => {
    openMenu();

    const tasks = Array.from(
      fixture.nativeElement.querySelectorAll('[role="option"]') as NodeListOf<HTMLButtonElement>,
    ).find((option) => option.textContent?.trim() === 'Tasks');
    expect(tasks).toBeTruthy();

    tasks!.click();
    fixture.detectChanges();

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/home`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ value: { moduleId: 'tasks' } });
    req.flush({ key: 'home', value: { moduleId: 'tasks' } });

    expect(homePrefs.moduleId()).toBe('tasks');
    expect(trigger().textContent).toContain('Tasks');
    expect(fixture.nativeElement.querySelector('.type-select__menu')).toBeNull();
  });
});
