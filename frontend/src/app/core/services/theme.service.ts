import { DOCUMENT } from '@angular/common';
import { Injectable, Renderer2, RendererFactory2, inject, signal } from '@angular/core';

export type ThemePreference = 'system' | 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly renderer: Renderer2;
  private readonly storageKey = 'lifeos-theme';

  readonly preference = signal<ThemePreference>('system');

  constructor(rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
  }

  init(): void {
    const stored = this.readStoredPreference();
    this.preference.set(stored);
    this.applyTheme(stored);
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

  private applyTheme(preference: ThemePreference): void {
    const root = this.document.documentElement;
    this.renderer.removeClass(root, 'light');
    this.renderer.removeClass(root, 'dark');
    if (preference !== 'system') {
      this.renderer.addClass(root, preference);
    }
  }

  private readStoredPreference(): ThemePreference {
    const stored = localStorage.getItem(this.storageKey);
    return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system';
  }
}
