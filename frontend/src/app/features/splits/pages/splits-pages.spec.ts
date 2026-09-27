import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/services/auth.service';
import { DeviceSplitGroup, SplitBalances } from '../models/split.models';
import { SPLIT_DEVICE_STORAGE_KEY } from '../services/split-device-store.service';
import { groupView, member } from '../testing/split-fixtures';
import { SplitGroupPageComponent } from './split-group-page.component';
import { SplitsHomeComponent } from './splits-home.component';

const api = `${environment.apiUrl}/splits`;

function el(fixture: ComponentFixture<unknown>): HTMLElement {
  return fixture.nativeElement as HTMLElement;
}

function byTestId(fixture: ComponentFixture<unknown>, id: string): HTMLElement[] {
  return Array.from(el(fixture).querySelectorAll<HTMLElement>(`[data-testid="${id}"]`));
}

function saved(): DeviceSplitGroup[] {
  return JSON.parse(localStorage.getItem(SPLIT_DEVICE_STORAGE_KEY) ?? '[]') as DeviceSplitGroup[];
}

const settled: SplitBalances = { nets: [], debts: [] };

function seed(rows: DeviceSplitGroup[]): void {
  localStorage.setItem(SPLIT_DEVICE_STORAGE_KEY, JSON.stringify(rows));
}

describe('Split bills pages', () => {
  let http: HttpTestingController;

  function configure(code = 'k7mq2p', signedIn = false): void {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap({ code }) } } },
        { provide: AuthService, useValue: { isAuthenticated: signal(signedIn) } },
      ],
    });
    http = TestBed.inject(HttpTestingController);
  }

  function flushBalances(balances: SplitBalances = settled): void {
    http.expectOne(`${api}/groups/k7mq2p/balances`).flush(balances);
  }

  beforeEach(() => localStorage.removeItem(SPLIT_DEVICE_STORAGE_KEY));
  afterEach(() => {
    http.verify();
    localStorage.removeItem(SPLIT_DEVICE_STORAGE_KEY);
  });

  describe('SplitsHomeComponent', () => {
    function render(): ComponentFixture<SplitsHomeComponent> {
      const fixture = TestBed.createComponent(SplitsHomeComponent);
      fixture.detectChanges();
      return fixture;
    }

    it('create form shows the three expiry choices and the empty on-device hint', () => {
      configure();
      const fixture = render();
      const labels = byTestId(fixture, 'split-expiry-option').map((i) => i.parentElement!.textContent!.trim());
      expect(labels).toEqual([
        'This session (up to 12 h)',
        '1 hour',
        '6 hours',
        '24 hours',
        '3 days',
        '7 days',
        '30 days',
      ]);
      expect(el(fixture).textContent).toContain('Groups you create or join on this phone stay listed here.');
    });

    it('after create the short URL and group QR are on screen and the code is saved on this device', () => {
      configure();
      const fixture = render();
      fixture.componentInstance.create({ name: 'Dinner', creator_name: 'Asha', expiry: 'session' });
      const req = http.expectOne({ method: 'POST', url: `${api}/groups` });
      expect(req.request.body).toEqual({ name: 'Dinner', creator_name: 'Asha', expiry: 'session' });
      req.flush({
        code: 'k7mq2p',
        url_path: '/s/k7mq2p',
        member_id: 'm-a',
        seat_secret: 'secret-a',
        expires_at: '2026-09-27T22:00:00Z',
      });
      fixture.detectChanges();

      const url = `${location.origin}/s/k7mq2p`;
      const result = byTestId(fixture, 'split-create-result')[0];
      expect(result.textContent).toContain(url);
      expect(result.querySelector('[data-testid="split-group-qr"] svg')!.getAttribute('data-payload')).toBe(url);
      expect(saved()).toEqual([
        { code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-a', displayName: 'Asha', role: 'creator' },
      ]);
      // WhatsApp / Email are plain links built in the browser: no LifeOS call (verified in afterEach).
      const whatsapp = result.querySelector<HTMLAnchorElement>('[data-testid="split-whatsapp"]')!;
      const email = result.querySelector<HTMLAnchorElement>('[data-testid="split-email"]')!;
      expect(whatsapp.getAttribute('href')!.startsWith('https://wa.me/?text=')).toBeTrue();
      expect(whatsapp.getAttribute('href')).toContain(encodeURIComponent(url));
      expect(email.getAttribute('href')!.startsWith('mailto:')).toBeTrue();
      expect(email.getAttribute('href')).toContain(encodeURIComponent(url));
    });

    it('lists two saved codes with their URLs and an Open control each', () => {
      seed([
        { code: 'k7mq2p', name: 'Dinner', seatSecret: 's1', displayName: 'Asha', role: 'creator' },
        { code: 'abcdef', name: 'Trip', seatSecret: 's2', displayName: 'Asha', role: 'member' },
      ]);
      configure();
      const fixture = render();
      const rows = byTestId(fixture, 'split-device-row');
      expect(rows.length).toBe(2);
      expect(rows[0].textContent).toContain(`${location.origin}/s/k7mq2p`);
      expect(rows[1].textContent).toContain(`${location.origin}/s/abcdef`);
      const opens = byTestId(fixture, 'split-device-open');
      expect(opens.map((a) => a.getAttribute('href'))).toEqual(['/s/k7mq2p', '/s/abcdef']);
      // Each row reveals its own group QR on demand.
      expect(byTestId(fixture, 'split-group-qr').length).toBe(0);
      (rows[1].querySelector('[data-testid="split-qr-toggle"]') as HTMLButtonElement).click();
      fixture.detectChanges();
      const qr = byTestId(fixture, 'split-group-qr');
      expect(qr.length).toBe(1);
      expect(qr[0].querySelector('svg')!.getAttribute('data-payload')).toBe(`${location.origin}/s/abcdef`);
    });
  });

  describe('SplitGroupPageComponent', () => {
    function render(): ComponentFixture<SplitGroupPageComponent> {
      const fixture = TestBed.createComponent(SplitGroupPageComponent);
      fixture.detectChanges();
      return fixture;
    }

    it('sends the saved seat secret and shows the short URL with the group QR', () => {
      seed([{ code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-a', displayName: 'Asha', role: 'creator' }]);
      configure();
      const fixture = render();
      const req = http.expectOne(`${api}/groups/k7mq2p`);
      expect(req.request.headers.get('X-Split-Seat')).toBe('secret-a');
      req.flush(groupView({ my_member_id: 'm-a', is_creator: true }));
      flushBalances();
      fixture.detectChanges();

      const url = `${location.origin}/s/k7mq2p`;
      const header = byTestId(fixture, 'split-group-header')[0];
      expect(header.textContent).toContain(url);
      // The group QR sits behind "QR code" and can be shared or downloaded as an image.
      expect(header.querySelector('[data-testid="split-group-qr"]')).toBeNull();
      (header.querySelector('[data-testid="split-qr-toggle"]') as HTMLButtonElement).click();
      fixture.detectChanges();
      expect(header.querySelector('[data-testid="split-group-qr"] svg')!.getAttribute('data-payload')).toBe(url);
      expect(header.querySelector('[data-testid="split-qr-download"]')).not.toBeNull();
      expect(el(fixture).textContent).toContain('Share the link. People join only if they want to.');
      expect(byTestId(fixture, 'split-privacy-note')[0].textContent).toContain('erased when the link closes');
      // The page scrolls itself (the app root clips overflow), so bottom content stays reachable.
      expect(byTestId(fixture, 'split-page-scroll')[0].classList).toContain('overflow-y-auto');
    });

    it('after join in a second storage state, that list holds the code and the page shows the other bills', () => {
      // Browser B has never seen the group (its own empty storage state).
      configure();
      const fixture = render();
      const asha = member('m-a', 'Asha', 0);
      const dinner = {
        id: 'e-1',
        title: 'Dinner by Asha',
        amount_paise: 60000,
        paid_by: 'm-a',
        created_by: 'm-a',
        expense_date: '2026-09-27',
        created_at: '2026-09-27T10:05:00Z',
        shares: [{ member_id: 'm-a', amount_paise: 60000 }],
      };
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ expenses: [dinner] }));
      flushBalances();
      fixture.detectChanges();
      expect(byTestId(fixture, 'split-add').length).toBe(0);

      fixture.componentInstance.joinName.set('Bala');
      fixture.detectChanges();
      byTestId(fixture, 'split-join')[0].click();
      const join = http.expectOne({ method: 'POST', url: `${api}/groups/k7mq2p/join` });
      expect(join.request.body).toEqual({ display_name: 'Bala' });
      join.flush({ code: 'k7mq2p', url_path: '/s/k7mq2p', member_id: 'm-b', seat_secret: 'secret-b', expires_at: '' });

      expect(saved()).toEqual([
        { code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-b', displayName: 'Bala', role: 'member' },
      ]);
      const reload = http.expectOne(`${api}/groups/k7mq2p`);
      expect(reload.request.headers.get('X-Split-Seat')).toBe('secret-b');
      reload.flush(groupView({ members: [asha, member('m-b', 'Bala', 1)], expenses: [dinner], my_member_id: 'm-b' }));
      flushBalances();
      fixture.detectChanges();

      expect(byTestId(fixture, 'split-bill-row')[0].textContent).toContain('Dinner by Asha');
      expect(byTestId(fixture, 'split-join').length).toBe(0);
      expect(byTestId(fixture, 'split-add').length).toBe(1);
    });

    it('saves my UPI id before the bill when the add-split form carries one', () => {
      seed([{ code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-a', displayName: 'Asha', role: 'creator' }]);
      configure();
      const fixture = render();
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-a', is_creator: true }));
      flushBalances();
      const expense = { title: 'Tea', amount_rupees: 10, paid_by: 'm-a', member_ids: ['m-a'] };
      fixture.componentInstance.addSplit({ expense, upiVpa: 'asha@okbank' });

      const patch = http.expectOne({ method: 'PATCH', url: `${api}/groups/k7mq2p/members/me` });
      expect(patch.request.body).toEqual({ upi_vpa: 'asha@okbank' });
      expect(patch.request.headers.get('X-Split-Seat')).toBe('secret-a');
      patch.flush(member('m-a', 'Asha', 0, 'asha@okbank'));
      const post = http.expectOne({ method: 'POST', url: `${api}/groups/k7mq2p/expenses` });
      expect(post.request.body).toEqual(expense);
      post.flush({});
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-a', is_creator: true }));
      flushBalances();
    });

    it('marks a debt paid for its price with my seat, then confirms as the payee', () => {
      seed([{ code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-b', displayName: 'Bala', role: 'member' }]);
      configure();
      const fixture = render();
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-b' }));
      flushBalances();
      const debt = {
        payer_member_id: 'm-b',
        payer_name: 'Bala',
        payee_member_id: 'm-a',
        payee_name: 'Asha',
        outstanding_paise: 3334,
        pending_paise: 0,
        amount_paise: 3334,
        amount_rupees: '33.34',
        upi_uri: null,
      };
      fixture.componentInstance.markPaid({ debt, method: 'cash' });
      const post = http.expectOne({ method: 'POST', url: `${api}/groups/k7mq2p/settlements` });
      expect(post.request.body).toEqual({ payee_member_id: 'm-a', amount_rupees: 33.34, method: 'cash' });
      expect(post.request.headers.get('X-Split-Seat')).toBe('secret-b');
      post.flush({});
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-b' }));
      flushBalances();

      fixture.componentInstance.confirmPayment('s-1');
      const confirm = http.expectOne({ method: 'POST', url: `${api}/settlements/s-1/confirm` });
      expect(confirm.request.headers.get('X-Split-Seat')).toBe('secret-b');
      confirm.flush({});
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-b' }));
      flushBalances();
    });

    it('shows Keep in my history only to a signed-in seat holder whose history lacks the group', () => {
      seed([{ code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-b', displayName: 'Bala', role: 'member' }]);
      configure('k7mq2p', true);
      const fixture = render();
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-b', in_history: false }));
      flushBalances();
      fixture.detectChanges();
      byTestId(fixture, 'split-keep')[0].click();
      const keep = http.expectOne({ method: 'POST', url: `${api}/groups/k7mq2p/keep` });
      expect(keep.request.headers.get('X-Split-Seat')).toBe('secret-b');
      keep.flush(null);
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-b', in_history: true }));
      flushBalances();
      fixture.detectChanges();
      expect(byTestId(fixture, 'split-keep').length).toBe(0);
    });

    it('hides Keep for guests', () => {
      seed([{ code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-b', displayName: 'Bala', role: 'member' }]);
      configure();
      const fixture = render();
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-b', in_history: null }));
      flushBalances();
      fixture.detectChanges();
      expect(byTestId(fixture, 'split-keep').length).toBe(0);
    });

    it('lets the creator end an open link after confirming', () => {
      seed([{ code: 'k7mq2p', name: 'Dinner', seatSecret: 'secret-a', displayName: 'Asha', role: 'creator' }]);
      configure();
      const fixture = render();
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ my_member_id: 'm-a', is_creator: true }));
      flushBalances();
      fixture.detectChanges();
      expect(byTestId(fixture, 'split-end').length).toBe(0);
      byTestId(fixture, 'split-end-start')[0].click();
      fixture.detectChanges();
      byTestId(fixture, 'split-end')[0].click();
      const end = http.expectOne({ method: 'POST', url: `${api}/groups/k7mq2p/end` });
      expect(end.request.headers.get('X-Split-Seat')).toBe('secret-a');
      end.flush(null);
      const ended = groupView({ my_member_id: 'm-a', is_creator: true, is_open: false, ended_at: '2026-09-27T11:00:00Z' });
      http.expectOne(`${api}/groups/k7mq2p`).flush(ended);
      flushBalances();
      fixture.detectChanges();
      expect(byTestId(fixture, 'split-end-start').length).toBe(0);
      expect(byTestId(fixture, 'split-add').length).toBe(0);
      expect(byTestId(fixture, 'split-link-status')[0].textContent).toContain('Link ended');
    });

    it('closed link: a visitor can read but not join', () => {
      configure();
      const fixture = render();
      http.expectOne(`${api}/groups/k7mq2p`).flush(groupView({ is_open: false }));
      flushBalances();
      fixture.detectChanges();
      expect(byTestId(fixture, 'split-join').length).toBe(0);
      expect(el(fixture).textContent).toContain('This link is closed. You can still read the group.');
    });

    it('opens without a seat for a visitor', () => {
      configure();
      render();
      const req = http.expectOne(`${api}/groups/k7mq2p`);
      expect(req.request.headers.has('X-Split-Seat')).toBeFalse();
      req.flush(groupView());
      flushBalances();
    });
  });
});
