import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { SettingsHubComponent } from './settings-hub.component';
import {
  SETTINGS_CATEGORIES,
  SETTINGS_SECTIONS,
  SettingsSection,
  groupSettingsSections,
  resolveSettingsSection,
} from './settings-sections';

describe('settings section registry', () => {
  it('has unique ids in known categories', () => {
    const ids = SETTINGS_SECTIONS.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const s of SETTINGS_SECTIONS) {
      expect(SETTINGS_CATEGORIES).toContain(s.category);
    }
  });

  it('resolves fragments, legacy aliases, and unknown values', () => {
    expect(resolveSettingsSection('export').id).toBe('export');
    expect(resolveSettingsSection('notifications').id).toBe('integrations');
    expect(resolveSettingsSection('nope').id).toBe('profile');
    expect(resolveSettingsSection(null).id).toBe('profile');
  });

  it('places a new entry in its category without other changes', () => {
    const extra: SettingsSection = { id: 'privacy', label: 'Privacy', category: 'Account' };
    const account = groupSettingsSections([...SETTINGS_SECTIONS, extra]).find((g) => g.category === 'Account');
    expect(account?.sections.map((s) => s.id)).toEqual(['profile', 'password', 'privacy']);
  });
});

describe('SettingsHubComponent', () => {
  let fixture: ComponentFixture<SettingsHubComponent>;
  const fragment$ = new BehaviorSubject<string | null>('editor');

  beforeEach(async () => {
    localStorage.clear();
    fragment$.next('editor');
    await TestBed.configureTestingModule({
      imports: [SettingsHubComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    })
      .overrideProvider(ActivatedRoute, {
        useValue: { fragment: fragment$.asObservable(), snapshot: { fragment: 'editor' } },
      })
      .compileComponents();

    fixture = TestBed.createComponent(SettingsHubComponent);
    fixture.detectChanges();
  });

  afterEach(() => localStorage.clear());

  function el(): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  it('renders nav and picker entries for every registered section', () => {
    expect(el().querySelectorAll('.settings-nav__item').length).toBe(SETTINGS_SECTIONS.length);
    expect(el().querySelectorAll('#settings-section-picker option').length).toBe(SETTINGS_SECTIONS.length);
    expect(el().querySelectorAll('#settings-section-picker optgroup').length).toBe(groupSettingsSections().length);
  });

  it('shows only the section named by the fragment and marks it active', () => {
    expect(el().querySelector('section#editor')).toBeTruthy();
    expect(el().querySelector('app-settings-editor-section')).toBeTruthy();
    expect(el().querySelector('app-settings-currency-section')).toBeNull();
    expect(el().querySelector('.settings-nav__item--active')?.textContent?.trim()).toBe('Editor');
  });

  it('switches sections when the fragment changes, including legacy aliases', () => {
    fragment$.next('currency');
    fixture.detectChanges();
    expect(el().querySelector('app-settings-currency-section')).toBeTruthy();
    expect(el().querySelector('app-settings-editor-section')).toBeNull();

    fragment$.next('notifications');
    fixture.detectChanges();
    expect(el().querySelector('section#integrations')).toBeTruthy();
  });
});
