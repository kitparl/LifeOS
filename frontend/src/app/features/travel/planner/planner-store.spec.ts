import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed, fakeAsync, flushMicrotasks, tick } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { MyPlan, PlanDocument, PublicPlanView } from '../models/share.models';
import { addStop, newStop } from './plan-ops';
import { plannerStorage } from './planner-identity';
import { PlannerStore, SAVE_DELAY_MS } from './planner-store';

const CODE = 'k7mq2p3x';
const BASE = `${environment.apiUrl}/travel/shared/${CODE}`;

const original: PlanDocument = {
  schema_version: 1,
  days: [{ title: null, notes: null, stops: [newStop({ title: 'Manali' })] }],
};
const view = (patch: Partial<PublicPlanView> = {}): PublicPlanView => ({
  trip: { name: 'Himachal 2027', description: null, start_date: '2027-06-12', end_date: '2027-06-21' },
  owner_name: 'Priya',
  state: 'open',
  names_allowed: true,
  google_enabled: true,
  is_final: false,
  viewer_is_owner: false,
  manage_path: null,
  plan: original,
  limits: { max_days: 120, max_stops: 500 },
  ...patch,
});
const myPlan = (revision: number, document = original): MyPlan => ({
  id: 'v1',
  status: 'draft',
  revision,
  updated_at: '2026-10-12T10:00:00Z',
  submitted_at: null,
  edited_since_sent: false,
  document,
});
const joined = { token: 'tok', expires_at: '2099-01-01T00:00:00Z', device_secret: 's'.repeat(32), contributor: { id: 'c1', kind: 'name', display_name: 'Asha' }, plan: null };

function clearPlannerStorage(): void {
  for (const key of [`tp:${CODE}`, `tp:${CODE}:draft`, 'tp:first-run']) localStorage.removeItem(key);
  sessionStorage.removeItem(`tp:${CODE}:token`);
}

describe('PlannerStore', () => {
  let store: PlannerStore;
  let http: HttpTestingController;

  beforeEach(() => {
    clearPlannerStorage();
    TestBed.configureTestingModule({ providers: [PlannerStore, provideHttpClient(), provideHttpClientTesting()] });
    store = TestBed.inject(PlannerStore);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    clearPlannerStorage();
  });

  function load(v = view()): void {
    void store.load(CODE);
    http.expectOne(BASE).flush(v);
    flushMicrotasks();
  }

  /** Join with a name and start the friend's plan (the first edit does both). */
  function joinAndStart(): void {
    void store.joinWithName('Asha');
    http.expectOne(`${BASE}/join/name`).flush(joined);
    flushMicrotasks();
  }

  it('shows the trip plan and asks nothing until the first change', fakeAsync(() => {
    load();
    expect(store.mode()).toBe('viewing');
    expect(store.shown()).toEqual(original);
    expect(store.askWho()).toBeFalse();

    void store.edit((d) => addStop(d, 0, newStop({ title: 'Cafe' })));
    flushMicrotasks();
    expect(store.askWho()).toBeTrue();
    http.expectNone(`${BASE}/me/plan`);

    joinAndStart();
    const start = http.expectOne({ method: 'POST', url: `${BASE}/me/plan` });
    expect(start.request.headers.get('X-Share-Token')).toBe('tok');
    expect(start.request.headers.has('Authorization')).toBeFalse();
    start.flush(myPlan(1));
    flushMicrotasks();
    expect(store.mode()).toBe('editing');
    expect(store.doc()!.days[0].stops.map((s) => s.title)).toEqual(['Manali', 'Cafe']);
    expect(plannerStorage.identity(CODE)?.contributor.display_name).toBe('Asha');
    tick(SAVE_DELAY_MS);
    http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` }).flush(myPlan(2));
  }));

  it('autosaves: Saving, then Saved, with the confirmed revision in If-Match', fakeAsync(() => {
    load();
    joinAndStart();
    void store.edit((d) => d);
    http.expectOne(`${BASE}/me/plan`).flush(myPlan(1));
    flushMicrotasks();
    void store.edit((d) => addStop(d, 0, newStop({ title: 'Lake' })));
    flushMicrotasks();
    expect(store.saveState()).toBe('saving');
    expect(plannerStorage.draft(CODE)).not.toBeNull(); // the friend's text is safe before the server has it

    tick(SAVE_DELAY_MS);
    const put = http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` });
    expect(put.request.headers.get('If-Match')).toBe('"1"');
    put.flush(myPlan(2));
    expect(store.saveState()).toBe('saved');
    expect(plannerStorage.draft(CODE)).toBeNull();
  }));

  it('goes "Offline, will retry" and saves when the network is back', fakeAsync(() => {
    load();
    joinAndStart();
    void store.edit((d) => d);
    http.expectOne(`${BASE}/me/plan`).flush(myPlan(1));
    flushMicrotasks();
    tick(SAVE_DELAY_MS);
    http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` }).error(new ProgressEvent('offline'), { status: 0 });
    expect(store.saveState()).toBe('offline');
    expect(store.pending()).toBeTrue();

    tick(2000);
    http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` }).flush(myPlan(2));
    expect(store.saveState()).toBe('saved');
  }));

  it('never silently overwrites another device: 412 asks the friend', fakeAsync(() => {
    load();
    joinAndStart();
    void store.edit((d) => d);
    http.expectOne(`${BASE}/me/plan`).flush(myPlan(1));
    flushMicrotasks();
    tick(SAVE_DELAY_MS);
    http
      .expectOne({ method: 'PUT', url: `${BASE}/me/plan` })
      .flush({ detail: { code: 'stale', revision: 5 } }, { status: 412, statusText: 'Precondition Failed' });
    expect(store.saveState()).toBe('conflict');

    store.keepMine();
    const retry = http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` });
    expect(retry.request.headers.get('If-Match')).toBe('"5"');
    retry.flush(myPlan(6));
    expect(store.saveState()).toBe('saved');
  }));

  it('undoes a removal and saves the undo too', fakeAsync(() => {
    load();
    joinAndStart();
    void store.edit((d) => d);
    http.expectOne(`${BASE}/me/plan`).flush(myPlan(1));
    flushMicrotasks();
    void store.removeWithUndo((d) => ({ ...d, days: [{ ...d.days[0], stops: [] }] }), 'Removed Manali');
    flushMicrotasks();
    expect(store.toast()).toEqual({ message: 'Removed Manali', undo: true });
    expect(store.doc()!.days[0].stops.length).toBe(0);

    store.undo();
    expect(store.doc()!.days[0].stops.map((s) => s.title)).toEqual(['Manali']);
    expect(store.toast()).toBeNull();
    tick(SAVE_DELAY_MS);
    const put = http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` });
    expect((put.request.body as PlanDocument).days[0].stops.length).toBe(1);
    put.flush(myPlan(2));
  }));

  it('sends after the last change is saved', fakeAsync(() => {
    load();
    joinAndStart();
    void store.edit((d) => d);
    http.expectOne(`${BASE}/me/plan`).flush(myPlan(1));
    flushMicrotasks();
    let sent: boolean | undefined;
    void store.send('Added a cafe').then((ok) => (sent = ok));
    flushMicrotasks();
    http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` }).flush(myPlan(2));
    flushMicrotasks();
    const submit = http.expectOne(`${BASE}/me/plan/submit`);
    expect(submit.request.body).toEqual({ message: 'Added a cafe' });
    submit.flush({ ...myPlan(2), status: 'submitted' });
    flushMicrotasks();
    expect(sent).toBeTrue();
    expect(store.mine()?.status).toBe('submitted');
  }));

  it('is read-only once the plan is final', fakeAsync(() => {
    load(view({ state: 'locked', is_final: true }));
    expect(store.mode()).toBe('locked');
    void store.edit((d) => addStop(d, 0, newStop({ title: 'Cafe' })));
    flushMicrotasks();
    expect(store.askWho()).toBeFalse();
    http.expectNone(() => true);
  }));

  it('explains an unknown or turned-off link', fakeAsync(() => {
    void store.load(CODE);
    http.expectOne(BASE).flush({ detail: 'gone' }, { status: 410, statusText: 'Gone' });
    flushMicrotasks();
    expect(store.mode()).toBe('unavailable');
    expect(store.unavailable()).toBe('gone');
  }));

  describe('road km and the PDF', () => {
    const routable: PlanDocument = {
      schema_version: 1,
      days: [
        {
          title: null,
          notes: null,
          stops: [
            newStop({ title: 'Manali', place: { name: 'Manali', lat: 32.2432, lng: 77.1892 } }),
            newStop({ title: 'Hampta', place: { name: 'Hampta', lat: 32.2667, lng: 77.3667 } }),
          ],
        },
      ],
    };

    it('fetches road km for a day with the friend\'s token and saves the route in their plan', fakeAsync(() => {
      load(view({ plan: routable }));
      expect(store.facts()!.days[0]).toEqual(jasmine.objectContaining({ approx: true, canRoute: true }));
      joinAndStart();
      let ok: boolean | undefined;
      void store.roadKm(0).then((r) => (ok = r));
      const route = http.expectOne({ method: 'POST', url: `${BASE}/route` });
      expect(route.request.headers.get('X-Share-Token')).toBe('tok');
      expect(route.request.body).toEqual({ points: [[32.2432, 77.1892], [32.2667, 77.3667]] });
      expect(store.routingDay()).toBe(0);
      route.flush({ mode: 'driving', legs: [{ distance_m: 51_000, duration_s: 3_100, polyline: '' }], fallback_reason: null });
      flushMicrotasks();
      http.expectOne({ method: 'POST', url: `${BASE}/me/plan` }).flush(myPlan(1, routable));
      flushMicrotasks();

      expect(ok).toBeTrue();
      expect(store.routingDay()).toBeNull();
      expect(store.facts()!.days[0]).toEqual(jasmine.objectContaining({ meters: 51_000, seconds: 3_100, road: true, canRoute: false }));
      tick(SAVE_DELAY_MS);
      const put = http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` });
      expect((put.request.body as PlanDocument).days[0].route?.legs[0].distance_m).toBe(51_000);
      put.flush(myPlan(2));
    }));

    it('keeps the estimates when the link has used up its road km for today', fakeAsync(() => {
      load(view({ plan: routable }));
      joinAndStart();
      let ok: boolean | undefined;
      void store.roadKm(0).then((r) => (ok = r));
      http.expectOne(`${BASE}/route`).flush({ mode: 'driving', legs: [], fallback_reason: 'guest_limit' });
      flushMicrotasks();
      expect(ok).toBeFalse();
      expect(store.facts()!.days[0].approx).toBeTrue();
      http.expectNone(`${BASE}/me/plan`);
    }));

    it('downloads the shared plan, or the friend\'s own plan once it is saved', fakeAsync(() => {
      load();
      let blob: Blob | undefined;
      void store.pdf().then((b) => (blob = b));
      const shown = http.expectOne(`${BASE}/pdf`);
      expect(shown.request.headers.has('X-Share-Token')).toBeFalse();
      shown.flush(new Blob(['%PDF']));
      flushMicrotasks();
      expect(blob).toBeTruthy();

      joinAndStart();
      void store.edit((d) => addStop(d, 0, newStop({ title: 'Cafe' })));
      http.expectOne(`${BASE}/me/plan`).flush(myPlan(1));
      flushMicrotasks();
      void store.pdf();
      flushMicrotasks();
      http.expectOne({ method: 'PUT', url: `${BASE}/me/plan` }).flush(myPlan(2)); // saved first
      flushMicrotasks();
      const mine = http.expectOne(`${BASE}/me/plan/pdf`);
      expect(mine.request.headers.get('X-Share-Token')).toBe('tok');
      mine.flush(new Blob(['%PDF']));
      flushMicrotasks();
    }));
  });
});
