import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { NAV_LUCIDE_ICON_PROVIDERS } from './nav-lucide';
import { NotificationDropdownComponent } from './notification-dropdown.component';

describe('NotificationDropdownComponent', () => {
  let fixture: ComponentFixture<NotificationDropdownComponent>;
  let http: HttpTestingController;
  let router: Router;
  const api = `${environment.apiUrl}/notifications`;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NotificationDropdownComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'notifications', children: [] }, { path: 'tasks', children: [] }]),
        ...NAV_LUCIDE_ICON_PROVIDERS,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NotificationDropdownComponent);
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    // Router NavigationEnd triggers a refresh; drain any leftover unread polls.
    http.match((r) => r.url === api && r.params.get('unread_only') === 'true').forEach((r) => {
      r.flush([], { headers: { 'X-Total-Count': '0' } });
    });
    http.verify();
  });

  function flushUnread(total: number): void {
    const req = http.expectOne(
      (r) => r.url === api && r.params.get('unread_only') === 'true' && r.params.get('limit') === '1',
    );
    req.flush([], { headers: { 'X-Total-Count': String(total) } });
  }

  function flushPreview(items: unknown[]): void {
    const req = http.expectOne(
      (r) => r.url === api && r.params.get('unread_only') === 'false' && r.params.get('limit') === '8',
    );
    req.flush(items, { headers: { 'X-Total-Count': String(items.length) } });
  }

  function sampleNotification(overrides: Partial<Record<string, unknown>> = {}) {
    return {
      id: 'n1',
      message: 'New task assigned',
      module: 'tasks',
      entity_id: null,
      route: '/tasks',
      is_read: false,
      channel: 'in_app',
      telegram_sent: false,
      created_at: '2026-09-19T10:00:00Z',
      ...overrides,
    };
  }

  it('should hide badge when unread count is zero', () => {
    fixture.detectChanges();
    flushUnread(0);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-badge"]')).toBeNull();
  });

  it('should show 9+ when unread count exceeds 9', () => {
    fixture.detectChanges();
    flushUnread(12);
    fixture.detectChanges();
    const badge = fixture.nativeElement.querySelector('[data-testid="notification-badge"]');
    expect(badge).toBeTruthy();
    expect(badge.textContent.trim()).toBe('9+');
  });

  it('should open panel on bell click and show empty state', () => {
    fixture.detectChanges();
    flushUnread(0);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('[data-testid="notification-bell"]').click();
    fixture.detectChanges();
    flushPreview([]);
    flushUnread(0);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[data-testid="notification-panel"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-empty"]').textContent).toContain(
      'No notifications',
    );
  });

  it('should navigate to /notifications when More is clicked', fakeAsync(() => {
    fixture.detectChanges();
    flushUnread(1);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('[data-testid="notification-bell"]').click();
    fixture.detectChanges();
    flushPreview([sampleNotification()]);
    flushUnread(1);
    fixture.detectChanges();

    const navigateSpy = spyOn(router, 'navigateByUrl').and.returnValue(Promise.resolve(true));
    fixture.nativeElement.querySelector('[data-testid="notification-more"]').click();
    tick();
    fixture.detectChanges();

    expect(navigateSpy).toHaveBeenCalledWith('/notifications');
    expect(fixture.nativeElement.querySelector('[data-testid="notification-panel"]')).toBeNull();
  }));

  it('should mark read and navigate when a row with route is clicked', fakeAsync(() => {
    fixture.detectChanges();
    flushUnread(1);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('[data-testid="notification-bell"]').click();
    fixture.detectChanges();
    flushPreview([sampleNotification()]);
    flushUnread(1);
    fixture.detectChanges();

    const navigateSpy = spyOn(router, 'navigateByUrl').and.returnValue(Promise.resolve(true));
    fixture.nativeElement.querySelector('.notif-row').click();

    const patch = http.expectOne(`${api}/n1/read`);
    expect(patch.request.method).toBe('PATCH');
    patch.flush({ ...sampleNotification(), is_read: true });
    flushUnread(0);
    tick();
    fixture.detectChanges();

    expect(navigateSpy).toHaveBeenCalledWith('/tasks');
  }));

  it('should update badge after mark all as read', () => {
    fixture.detectChanges();
    flushUnread(3);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-badge"]').textContent.trim()).toBe(
      '3',
    );

    fixture.nativeElement.querySelector('[data-testid="notification-bell"]').click();
    fixture.detectChanges();
    flushPreview([sampleNotification()]);
    flushUnread(3);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('[data-testid="notification-mark-all"]').click();
    const post = http.expectOne(`${api}/mark-all-read`);
    expect(post.request.method).toBe('POST');
    post.flush(null, { status: 204, statusText: 'No Content' });
    flushPreview([]);
    fixture.detectChanges();

    expect(fixture.componentInstance.unreadCount()).toBe(0);
    expect(fixture.nativeElement.querySelector('[data-testid="notification-badge"]')).toBeNull();
  });

  it('should close on Escape', () => {
    fixture.detectChanges();
    flushUnread(0);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('[data-testid="notification-bell"]').click();
    fixture.detectChanges();
    flushPreview([]);
    flushUnread(0);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-panel"]')).toBeTruthy();

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-panel"]')).toBeNull();
  });

  it('should not open on hover alone', () => {
    fixture.detectChanges();
    flushUnread(0);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('.notif-wrap').dispatchEvent(new Event('mouseenter'));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-panel"]')).toBeNull();
  });

  it('should close when the pointer leaves the wrap', fakeAsync(() => {
    fixture.detectChanges();
    flushUnread(0);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('[data-testid="notification-bell"]').click();
    fixture.detectChanges();
    flushPreview([]);
    flushUnread(0);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-panel"]')).toBeTruthy();

    fixture.nativeElement.querySelector('.notif-wrap').dispatchEvent(new Event('mouseleave'));
    tick(120);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="notification-panel"]')).toBeNull();
  }));
});
