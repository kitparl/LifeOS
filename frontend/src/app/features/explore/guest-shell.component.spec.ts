import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../../shared/layout/nav-lucide';
import { GuestShellComponent } from './guest-shell.component';
import { EXPLORE_TOOLS } from './explore-tools.registry';

describe('GuestShellComponent', () => {
  function render(): HTMLElement {
    TestBed.configureTestingModule({
      imports: [GuestShellComponent],
      providers: [provideRouter([]), ...NAV_LUCIDE_ICON_PROVIDERS],
    });
    const fixture = TestBed.createComponent(GuestShellComponent);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('renders a nav entry for every registered free tool', () => {
    const el = render();
    for (const tool of EXPLORE_TOOLS) {
      expect(el.querySelector(`[data-testid="guest-shell-nav-${tool.id}"]`)).not.toBeNull();
      expect(el.querySelector(`[data-testid="guest-shell-mobile-nav-${tool.id}"]`)).not.toBeNull();
    }
  });

  it('lists News alongside Developer', () => {
    const el = render();
    expect(el.querySelector('[data-testid="guest-shell-nav-news"]')?.getAttribute('href')).toBe('/explore/news');
    expect(el.querySelector('[data-testid="guest-shell-nav-developer"]')).not.toBeNull();
  });

  it('offers Sign in links to /login', () => {
    const el = render();
    for (const id of ['guest-shell-header-sign-in', 'guest-shell-sidebar-sign-in', 'guest-shell-mobile-sign-in']) {
      expect(el.querySelector(`[data-testid="${id}"]`)?.getAttribute('href')).toBe('/login');
    }
  });

  it('has no authenticated-only chrome', () => {
    const el = render();
    for (const selector of [
      'app-ai-chat-panel',
      'app-notification-dropdown',
      'app-word-of-the-day-chip',
      'app-command-palette',
    ]) {
      expect(el.querySelector(selector)).toBeNull();
    }
    const text = el.textContent ?? '';
    expect(text).not.toContain('Log out');
    expect(text).not.toContain('Assistant');
    expect(text).not.toContain('⌘K');
  });
});
