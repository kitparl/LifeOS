import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { DeviceSplitGroup } from '../models/split.models';
import { SPLIT_DEVICE_STORAGE_KEY } from '../services/split-device-store.service';
import { groupView } from '../testing/split-fixtures';
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

function seed(rows: DeviceSplitGroup[]): void {
  localStorage.setItem(SPLIT_DEVICE_STORAGE_KEY, JSON.stringify(rows));
}

describe('Split bills pages', () => {
  let http: HttpTestingController;

  function configure(code = 'k7mq2p'): void {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap({ code }) } } },
      ],
    });
    http = TestBed.inject(HttpTestingController);
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
      expect(labels).toEqual(['This session', '24 hours', '7 days']);
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
      fixture.detectChanges();

      const url = `${location.origin}/s/k7mq2p`;
      const header = byTestId(fixture, 'split-group-header')[0];
      expect(header.textContent).toContain(url);
      expect(header.querySelector('[data-testid="split-group-qr"] svg')!.getAttribute('data-payload')).toBe(url);
      expect(el(fixture).textContent).toContain('Share the link. People join only if they want to.');
    });

    it('opens without a seat for a visitor', () => {
      configure();
      render();
      const req = http.expectOne(`${api}/groups/k7mq2p`);
      expect(req.request.headers.has('X-Split-Seat')).toBeFalse();
      req.flush(groupView());
    });
  });
});
