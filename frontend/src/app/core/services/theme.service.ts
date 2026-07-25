import { DOCUMENT } from '@angular/common';
import { Injectable, Renderer2, RendererFactory2, inject, signal } from '@angular/core';

export type ThemePreference = 'system' | 'light' | 'dark';

/** Light window in local user timezone: inclusive start hour, exclusive end hour. */
const LIGHT_START_HOUR = 6;
const LIGHT_END_HOUR = 19;
const DEFAULT_TIMEZONE = 'Asia/Kolkata';
const RECHECK_MS = 5 * 60 * 1000;

/**
 * ThemeService — light / dark / Auto.
 *
 * Auto (`system`) resolves by time-of-day in the user's timezone
 * (default Asia/Kolkata): light 06:00–19:00, dark otherwise.
 * Explicit Light/Dark override Auto.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly renderer: Renderer2;
  private readonly storageKey = 'lifeos-theme';
  private timezone = DEFAULT_TIMEZONE;
  private recheckTimer: ReturnType<typeof setInterval> | null = null;
  private visibilityHandler: (() => void) | null = null;

  readonly preference = signal<ThemePreference>('system');

  constructor(rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
  }

  init(): void {
    const stored = this.readStoredPreference();
    this.preference.set(stored);
    this.applyTheme(stored);
    this.startRecheck();
  }

  /** Optional: call when user profile timezone is known. */
  setTimezone(tz: string | null | undefined): void {
    this.timezone = (tz || '').trim() || DEFAULT_TIMEZONE;
    if (this.preference() === 'system') {
      this.applyTheme('system');
    }
  }

  setPreference(preference: ThemePreference): void {
    this.preference.set(preference);
    localStorage.setItem(this.storageKey, preference);
    this.applyTheme(preference);
  }

  cyclePreference(): void {
    const current = this.preference();
    const next: ThemePreference =
      current === 'system' ? 'light' : current === 'light' ? 'dark' : 'system';
    this.setPreference(next);
  }

  label(): string {
    const current = this.preference();
    return current === 'system' ? 'Auto' : current === 'light' ? 'Light' : 'Dark';
  }

  private startRecheck(): void {
    if (this.recheckTimer) {
      clearInterval(this.recheckTimer);
    }
    this.recheckTimer = setInterval(() => {
      if (this.preference() === 'system') {
        this.applyTheme('system');
      }
    }, RECHECK_MS);

    if (this.visibilityHandler) {
      this.document.removeEventListener('visibilitychange', this.visibilityHandler);
    }
    this.visibilityHandler = () => {
      if (this.document.visibilityState === 'visible' && this.preference() === 'system') {
        this.applyTheme('system');
      }
    };
    this.document.addEventListener('visibilitychange', this.visibilityHandler);
  }

  private applyTheme(preference: ThemePreference): void {
    const root = this.document.documentElement;
    this.renderer.removeClass(root, 'light');
    this.renderer.removeClass(root, 'dark');
    const resolved = preference === 'system' ? this.resolveTimeOfDay() : preference;
    this.renderer.addClass(root, resolved);
  }

  private resolveTimeOfDay(): 'light' | 'dark' {
    const hour = this.currentHourInTimezone(this.timezone);
    if (hour >= LIGHT_START_HOUR && hour < LIGHT_END_HOUR) {
      return 'light';
    }
    return 'dark';
  }

  private currentHourInTimezone(tz: string): number {
    try {
      const parts = new Intl.DateTimeFormat('en-GB', {
        timeZone: tz,
        hour: 'numeric',
        hour12: false,
        hourCycle: 'h23',
      }).formatToParts(new Date());
      const hourPart = parts.find((p) => p.type === 'hour');
      const hour = hourPart ? Number.parseInt(hourPart.value, 10) : NaN;
      if (!Number.isNaN(hour)) {
        return hour === 24 ? 0 : hour;
      }
    } catch {
      /* fall through */
    }
    return new Date().getHours();
  }

  private readStoredPreference(): ThemePreference {
    const stored = localStorage.getItem(this.storageKey);
    return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system';
  }
}
