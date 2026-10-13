import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Component, input } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, flushMicrotasks } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { PlanDocument, PublicPlanView } from '../models/share.models';
import { newStop } from './plan-ops';
import { PlannerMapComponent } from './components/planner-map.component';
import { PlannerPageComponent } from './planner-page.component';
import { plannerStorage } from './planner-identity';

/** Specs never load Leaflet: the map is replaced by an empty stand-in. */
@Component({ selector: 'app-planner-map', standalone: true, template: '' })
class MapStubComponent {
  readonly plan = input<PlanDocument | null>(null);
}

const CODE = 'k7mq2p3x';
const BASE = `${environment.apiUrl}/travel/shared/${CODE}`;
const plan: PlanDocument = {
  schema_version: 1,
  days: [
    { title: 'Arrive', notes: null, stops: [newStop({ title: 'Manali' }), newStop({ title: 'Hampta Pass' })] },
    { title: null, notes: null, stops: [] },
  ],
};
const view = (patch: Partial<PublicPlanView> = {}): PublicPlanView => ({
  trip: { name: 'Himachal 2027', description: null, start_date: '2027-06-12', end_date: '2027-06-13' },
  owner_name: 'Priya',
  state: 'open',
  names_allowed: true,
  google_enabled: false,
  is_final: false,
  viewer_is_owner: false,
  manage_path: null,
  plan,
  limits: { max_days: 120, max_stops: 500 },
  ...patch,
});

function clearPlannerStorage(): void {
  for (const key of [`tp:${CODE}`, `tp:${CODE}:draft`, 'tp:first-run']) localStorage.removeItem(key);
  sessionStorage.removeItem(`tp:${CODE}:token`);
}

describe('PlannerPageComponent', () => {
  let fixture: ComponentFixture<PlannerPageComponent>;
  let http: HttpTestingController;
  let el: HTMLElement;

  beforeEach(() => {
    clearPlannerStorage();
    plannerStorage.setFirstRunDone();
    TestBed.configureTestingModule({
      imports: [PlannerPageComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap({ code: CODE }) } } },
      ],
    });
    TestBed.overrideComponent(PlannerPageComponent, {
      remove: { imports: [PlannerMapComponent] },
      add: { imports: [MapStubComponent] },
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(PlannerPageComponent);
    el = fixture.nativeElement;
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
    clearPlannerStorage();
  });

  function open(v: PublicPlanView): void {
    fixture.detectChanges();
    http.expectOne(BASE).flush(v);
    flushMicrotasks();
    fixture.detectChanges();
  }

  it('renders inside its own scoped root, with every day numbered and the plan in plain words', fakeAsync(() => {
    open(view());
    expect(el.querySelector('.tp-root')).not.toBeNull();
    expect(el.querySelectorAll('app-planner-day').length).toBe(2);
    expect(el.textContent).toContain('Day 1 · Arrive');
    expect(el.textContent).toContain("This is Priya's plan. Change anything to start your own.");
    expect(el.querySelectorAll('[data-testid="add-place"]').length).toBe(2);
    expect(document.head.querySelector('meta[name="referrer"]')?.getAttribute('content')).toBe('no-referrer');
  }));

  it('shows the final plan read-only: badge, explanation, no edit or send controls', fakeAsync(() => {
    open(view({ state: 'locked', is_final: true }));
    expect(el.querySelector('[data-testid="final-badge"]')).not.toBeNull();
    expect(el.querySelector('[data-testid="final-note"]')!.textContent).toContain('Priya has chosen the final plan');
    expect(el.querySelector('[data-testid="add-place"]')).toBeNull();
    expect(el.querySelector('[data-testid="stop-up"]')).toBeNull();
    expect(el.querySelector('[data-testid="send-open"]')).toBeNull();
  }));

  it('offers the owner a way to manage the plan in LifeOS', fakeAsync(() => {
    open(view({ viewer_is_owner: true, manage_path: '/travel/trips/t1?panel=share' }));
    const link = el.querySelector<HTMLAnchorElement>('[data-testid="owner-manage"]')!;
    expect(link.getAttribute('href')).toBe('/travel/trips/t1?panel=share');
  }));

  it('asks "Who are you?" on the first change, not before', fakeAsync(() => {
    open(view());
    expect(document.querySelector('[data-testid="who-name"]')).toBeNull();
    el.querySelector<HTMLButtonElement>('[data-testid="add-place"]')!.click();
    flushMicrotasks();
    fixture.detectChanges();
    expect(document.querySelector('[data-testid="who-name"]')).not.toBeNull();
  }));

  it('the toast Undo puts a removed stop back', fakeAsync(() => {
    open(view());
    const store = fixture.componentInstance.store;
    store.doc.set(plan);
    store.toast.set({ message: 'Removed Manali', undo: true });
    spyOn(store, 'undo');
    fixture.detectChanges();
    el.querySelector<HTMLButtonElement>('[data-testid="toast-undo"]')!.click();
    expect(store.undo).toHaveBeenCalled();
  }));

  it('explains a link that was turned off', fakeAsync(() => {
    fixture.detectChanges();
    http.expectOne(BASE).flush({ detail: 'gone' }, { status: 410, statusText: 'Gone' });
    flushMicrotasks();
    fixture.detectChanges();
    expect(el.querySelector('[data-testid="planner-unavailable"]')!.textContent).toContain('turned this link off');
  }));
});
