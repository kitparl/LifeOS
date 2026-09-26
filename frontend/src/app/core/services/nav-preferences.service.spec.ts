import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { NavPreferencesService, NavPrefsValue } from './nav-preferences.service';
import { DEFAULT_PINNED_IDS, NAV_CATEGORIES_ENABLED } from '../../shared/layout/nav-registry';
import { environment } from '../../../environments/environment';

const PREFS_URL = `${environment.apiUrl}/preferences/nav`;
const DEFAULT_HIDDEN_IDS = ['notifications', 'documents', 'search', 'memory', 'analytics', 'assistant'];

describe('NavPreferencesService', () => {
  let service: NavPreferencesService;
  let httpMock: HttpTestingController;

  const ids = (): string[] => service.pinnedDestinations().map((d) => d.id);

  function loadSaved(value: Partial<NavPrefsValue>): void {
    service.init();
    httpMock.expectOne(PREFS_URL).flush({ key: 'nav', value });
  }

  function flushSave(): void {
    httpMock.expectOne((r) => r.url === PREFS_URL && r.method === 'PUT').flush({});
  }

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(NavPreferencesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('has categories disabled', () => {
    expect(NAV_CATEGORIES_ENABLED).toBeFalse();
  });

  it('shows the default set with nothing pinned to top', () => {
    expect(ids()).toEqual(DEFAULT_PINNED_IDS);
    for (const id of DEFAULT_HIDDEN_IDS) {
      expect(service.isPinned(id)).withContext(id).toBeFalse();
    }
    expect(DEFAULT_PINNED_IDS.some((id) => service.isPinnedTop(id))).toBeFalse();
  });

  it('lists default-hidden modules in the Hidden list, but never Notifications', () => {
    const hidden = service.unpinnedDestinations().map((d) => d.id);
    expect(hidden).toEqual(jasmine.arrayContaining(['documents', 'search', 'memory', 'analytics', 'assistant']));
    expect(hidden).not.toContain('notifications');
  });

  it('renders a single flat group when nothing is pinned to top', () => {
    const groups = service.navGroups();
    expect(groups.length).toBe(1);
    expect(groups[0].items.map((d) => d.id)).toEqual(DEFAULT_PINNED_IDS);
  });

  it('keeps Notifications out of the sidebar even when saved prefs still show it', () => {
    loadSaved({ visible: ['notifications', 'tasks', 'documents'], pinnedTop: ['notifications'] });

    expect(ids()).toEqual(['tasks', 'documents']);
    expect(service.navGroups().flatMap((g) => g.items).map((d) => d.id)).not.toContain('notifications');
  });

  it('orders pinned modules first, then the visible order', () => {
    loadSaved({ visible: ['tasks', 'calendar', 'finance'], pinnedTop: ['finance'] });

    expect(ids()).toEqual(['finance', 'tasks', 'calendar']);
    expect(service.navGroups().map((g) => g.items.map((d) => d.id))).toEqual([['finance'], ['tasks', 'calendar']]);
  });

  it('reorders the flat group by rewriting the visible order', () => {
    loadSaved({ visible: ['tasks', 'calendar', 'finance'], pinnedTop: ['finance'] });
    const flat = service.navGroups()[1];

    service.reorderWithinCategory(flat.category, 1, 0);
    flushSave();

    expect(ids()).toEqual(['finance', 'calendar', 'tasks']);
  });

  it('appends a newly shown module to the end of the flat list', () => {
    service.pin('analytics');
    flushSave();

    expect(ids()).toEqual([...DEFAULT_PINNED_IDS, 'analytics']);
  });

  it('keeps category data when saving', () => {
    service.pin('documents');
    const req = httpMock.expectOne((r) => r.url === PREFS_URL && r.method === 'PUT');
    const body = req.request.body.value as NavPrefsValue;
    req.flush({});

    expect(body.categoryOrder.length).toBeGreaterThan(0);
    expect(body.moduleCategory['documents']).toBe('Knowledge');
    expect(body.order['Knowledge']).toContain('documents');
  });

  it('resets to the default set', () => {
    loadSaved({ visible: ['analytics', 'documents'], pinnedTop: ['analytics'] });

    service.resetToDefault();
    flushSave();

    expect(ids()).toEqual(DEFAULT_PINNED_IDS);
  });
});
