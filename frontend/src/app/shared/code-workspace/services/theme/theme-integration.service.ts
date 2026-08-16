import { Injectable, inject } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { Observable, Subscription } from 'rxjs';
import { ThemeService, ThemePreference } from '../../../../core/services/theme.service';

export type Theme = ThemePreference;

export interface EditorTheme {
  name: string;
  background: string;
  foreground: string;
  selection: string;
  cursor: string;
  lineHighlight: string;
  gutterBackground: string;
  gutterForeground: string;
}

@Injectable({ providedIn: 'root' })
export class ThemeIntegrationService {
  private readonly themeService = inject(ThemeService);

  readonly theme$: Observable<Theme> = toObservable(this.themeService.preference);
  readonly resolvedTheme$: Observable<'light' | 'dark'> = toObservable(this.themeService.resolved);

  getEditorTheme(theme: 'light' | 'dark'): EditorTheme {
    return {
      name: theme,
      background: 'var(--surface)',
      foreground: 'var(--text)',
      selection: 'var(--primary-soft)',
      cursor: 'var(--text)',
      lineHighlight: 'var(--surface-2)',
      gutterBackground: 'var(--surface)',
      gutterForeground: 'var(--text-muted)',
    };
  }

  getThemeVariables(theme: 'light' | 'dark'): Record<string, string> {
    const editor = this.getEditorTheme(theme);
    return {
      '--background': editor.background,
      '--text': editor.foreground,
      '--border': 'var(--border)',
      '--editor-background': editor.background,
      '--editor-foreground': editor.foreground,
      '--editor-selection': editor.selection,
      '--editor-cursor': editor.cursor,
      '--editor-line-highlight': editor.lineHighlight,
      '--editor-gutter-background': editor.gutterBackground,
      '--editor-gutter-foreground': editor.gutterForeground,
    };
  }

  subscribeToTheme(callback: (theme: 'light' | 'dark') => void): Subscription {
    return this.resolvedTheme$.subscribe(callback);
  }
}
