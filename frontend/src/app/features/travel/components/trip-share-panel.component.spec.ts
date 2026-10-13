import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../../../shared/layout/nav-lucide';
import { TripShare, VersionRow } from '../models/share.models';
import { TripSharePanelComponent } from './trip-share-panel.component';

const BASE = `${environment.apiUrl}/travel/trips/t1/share`;

const share = (patch: Partial<TripShare> = {}): TripShare => ({
  id: 's1',
  trip_id: 't1',
  code: 'k7mq2p3x',
  url_path: '/t/k7mq2p3x',
  state: 'open',
  require_google: false,
  allowed_emails: [],
  original_version_id: 'v0',
  locked_version_id: null,
  created_at: '2026-10-01T10:00:00Z',
  locked_at: null,
  revoked_at: null,
  contributors: [],
  ...patch,
});

const row = (id: string, label: string, patch: Partial<VersionRow> = {}): VersionRow => ({
  id,
  kind: 'plan',
  label,
  status: 'submitted',
  author_kind: 'contributor',
  author_name: label.split("'")[0],
  author_email: null,
  contributor_removed: false,
  is_locked: false,
  edited_since_sent: false,
  message: null,
  revision: 2,
  created_at: '2026-10-01T10:00:00Z',
  updated_at: '2026-10-02T10:00:00Z',
  submitted_at: '2026-10-02T10:00:00Z',
  summary: { days: 3, stops: 5, added: 1, removed: 0, changed: 2, km: 120 },
  ...patch,
});

describe('TripSharePanelComponent', () => {
  let fixture: ComponentFixture<TripSharePanelComponent>;
  let http: HttpTestingController;
  let el: HTMLElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TripSharePanelComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), ...NAV_LUCIDE_ICON_PROVIDERS],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(TripSharePanelComponent);
    fixture.componentRef.setInput('tripId', 't1');
    fixture.componentRef.setInput('tripName', 'Himachal 2027');
    fixture.componentRef.setInput('tripDays', 10);
    fixture.componentRef.setInput('tripStart', '2027-06-12');
    fixture.componentRef.setInput('startOpen', true);
    el = fixture.nativeElement;
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  function loadWith(s: TripShare, versions: VersionRow[]): void {
    http.expectOne(BASE).flush(s);
    http.expectOne(`${BASE}/versions`).flush(versions);
    fixture.detectChanges();
  }

  it('offers to create a link when the trip has none, saying what friends will see', () => {
    http.expectOne(BASE).flush({ detail: 'none' }, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();
    expect(el.textContent).toContain('including their notes');
    (el.querySelector('[data-testid="share-create"]') as HTMLButtonElement).click();
    http.expectOne({ method: 'POST', url: BASE }).flush(share());
    http.expectOne(`${BASE}/versions`).flush([row('v0', 'Original', { kind: 'original', status: 'draft' })]);
    fixture.detectChanges();
    expect(el.querySelector('[data-testid="trip-share-share-url"]')!.textContent).toContain('/t/k7mq2p3x');
  });

  it('lists versions in the server order (latest edited first) with word badges', () => {
    loadWith(share(), [
      row('v2', "Ravi's plan", { edited_since_sent: true }),
      row('v1', "Asha's plan", { status: 'draft', updated_at: '2026-10-01T12:00:00Z' }),
      row('v0', 'Original', { kind: 'original', status: 'draft', author_kind: 'system' }),
    ]);
    const items = Array.from(el.querySelectorAll('[data-testid^="version-v"]'));
    expect(items.map((i) => i.getAttribute('data-testid'))).toEqual(['version-v2', 'version-v1', 'version-v0']);
    const badges = Array.from(el.querySelectorAll('[data-testid="version-badge"]')).map((b) => b.textContent!.trim());
    expect(badges).toEqual(['Sent', 'Draft', 'Original']);
    expect(items[0].textContent).toContain('edited since sent');
    expect(items[0].querySelector('[data-testid="version-summary"]')!.textContent).toContain('1 added · 2 changed');
  });

  it('locks only after confirming, and applies by default', () => {
    const applied = jasmine.createSpy('applied');
    fixture.componentInstance.applied.subscribe(applied);
    loadWith(share(), [row('v2', "Ravi's plan", { summary: { days: 4, stops: 6, added: 1, removed: 0, changed: 0, km: 0 } })]);

    (el.querySelector('[data-testid="version-lock"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    http.expectNone(`${BASE}/lock`);
    const dialog = document.querySelector('[data-testid="lock-apply"]') as HTMLInputElement;
    expect(dialog.checked).toBeTrue();
    expect(document.querySelector('[data-testid="lock-end-date"]')!.textContent).toContain('4 days');

    (document.querySelector('[data-testid="lock-confirm"]') as HTMLButtonElement).click();
    const req = http.expectOne(`${BASE}/lock`);
    expect(req.request.body).toEqual({ version_id: 'v2', apply: true });
    req.flush({ share: share({ state: 'locked', locked_version_id: 'v2' }), applied: { days: 4 } });
    http.expectOne(`${BASE}/versions`).flush([row('v2', "Ravi's plan", { is_locked: true })]);
    fixture.detectChanges();
    expect(applied).toHaveBeenCalled();
    expect(el.querySelector('[data-testid="share-locked"]')).not.toBeNull();
    expect(el.querySelector('[data-testid="version-badge"]')!.textContent!.trim()).toBe('Final plan');
  });

  it('can lock without touching the trip', () => {
    loadWith(share(), [row('v2', "Ravi's plan")]);
    (el.querySelector('[data-testid="version-lock"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    (document.querySelector('[data-testid="lock-apply"]') as HTMLInputElement).click();
    fixture.detectChanges();
    (document.querySelector('[data-testid="lock-confirm"]') as HTMLButtonElement).click();
    expect(http.expectOne(`${BASE}/lock`).request.body).toEqual({ version_id: 'v2', apply: false });
  });
});
