import { Component, ViewEncapsulation } from '@angular/core';

/**
 * The trip planner's own design system: tokens and a few shared classes, all under `.tp-root`
 * so nothing reaches the LifeOS app and LifeOS theme classes do not reach in (requirements T-19).
 * Rendered once by the planner page; Angular removes these styles when the page is left.
 *
 * Tokens (light / dark follows the device, never the LifeOS theme):
 *   --tp-bg, --tp-surface, --tp-surface-2   page, cards, quiet fills
 *   --tp-text, --tp-muted                   body text (AA on bg and surface), secondary text
 *   --tp-accent, --tp-on-accent             warm terracotta actions and text on them
 *   --tp-border, --tp-focus                 hairlines, keyboard focus ring
 *   --tp-ok, --tp-warn, --tp-danger         saved, offline, remove
 *   --tp-day-1 .. --tp-day-8, --tp-on-day   day colours (always with the day number) and text on them
 *   --tp-font, --tp-text-base(16px), --tp-text-lg, --tp-text-xl
 *   --tp-radius(16px), --tp-radius-sm(10px), --tp-tap(44px min touch target), --tp-ease
 */
@Component({
  selector: 'app-planner-theme',
  standalone: true,
  template: '',
  encapsulation: ViewEncapsulation.None,
  styles: [
    `
      .tp-root {
        --tp-bg: #fff8f1; --tp-surface: #fff; --tp-surface-2: #fbefe3;
        --tp-text: #2b2118; --tp-muted: #6b5b4e; --tp-accent: #b93d0b; --tp-on-accent: #fff;
        --tp-border: #eadfd3; --tp-focus: #1d4ed8; --tp-ok: #15803d; --tp-warn: #a16207; --tp-danger: #b91c1c;
        --tp-day-1: #c2410c; --tp-day-2: #0e7490; --tp-day-3: #7c3aed; --tp-day-4: #15803d;
        --tp-day-5: #be185d; --tp-day-6: #a16207; --tp-day-7: #1d4ed8; --tp-day-8: #4d7c0f; --tp-on-day: #fff;
        --tp-font: ui-rounded, 'SF Pro Rounded', 'Segoe UI', system-ui, -apple-system, Roboto, sans-serif;
        --tp-text-base: 1rem; --tp-text-lg: 1.125rem; --tp-text-xl: 1.375rem;
        --tp-radius: 16px; --tp-radius-sm: 10px; --tp-tap: 44px; --tp-ease: 160ms ease;
        color-scheme: light;
        font-family: var(--tp-font);
        font-size: var(--tp-text-base);
        line-height: 1.5;
        color: var(--tp-text);
        background: var(--tp-bg);
        scrollbar-color: var(--tp-border) transparent;
      }
      @media (prefers-color-scheme: dark) {
        .tp-root {
          --tp-bg: #1c1714; --tp-surface: #27201c; --tp-surface-2: #33291f;
          --tp-text: #f6ede4; --tp-muted: #c9b8a8; --tp-accent: #fb923c; --tp-on-accent: #1c1714;
          --tp-border: #3a302a; --tp-focus: #93c5fd; --tp-ok: #4ade80; --tp-warn: #facc15; --tp-danger: #f87171;
          --tp-day-1: #fb923c; --tp-day-2: #22d3ee; --tp-day-3: #c4b5fd; --tp-day-4: #4ade80;
          --tp-day-5: #f9a8d4; --tp-day-6: #fde047; --tp-day-7: #93c5fd; --tp-day-8: #bef264; --tp-on-day: #1c1714;
          color-scheme: dark;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .tp-root { --tp-ease: 0ms linear; }
      }
      .tp-root *, .tp-root *::before, .tp-root *::after { box-sizing: border-box; }
      .tp-root :focus-visible { outline: 3px solid var(--tp-focus); outline-offset: 2px; }
      .tp-root h1, .tp-root h2, .tp-root h3, .tp-root p { margin: 0; }
      .tp-btn {
        display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
        min-height: var(--tp-tap); min-width: var(--tp-tap); padding: 0.5rem 1rem;
        border: 1px solid var(--tp-border); border-radius: 999px; background: var(--tp-surface);
        color: var(--tp-text); font: inherit; font-weight: 600; cursor: pointer;
        transition: background var(--tp-ease), transform var(--tp-ease);
      }
      .tp-btn:hover { background: var(--tp-surface-2); }
      .tp-btn:active { transform: scale(0.98); }
      .tp-btn:disabled { opacity: 0.55; cursor: default; }
      .tp-btn--primary { background: var(--tp-accent); border-color: var(--tp-accent); color: var(--tp-on-accent); }
      .tp-btn--primary:hover { background: var(--tp-accent); filter: brightness(1.08); }
      .tp-btn--quiet { border-color: transparent; background: transparent; }
      .tp-btn--block { width: 100%; }
      .tp-input {
        width: 100%; min-height: var(--tp-tap); padding: 0.625rem 0.875rem;
        border: 1px solid var(--tp-border); border-radius: var(--tp-radius-sm);
        background: var(--tp-surface); color: var(--tp-text); font: inherit;
      }
      .tp-label { display: block; margin-bottom: 0.25rem; font-weight: 600; }
      .tp-muted { color: var(--tp-muted); }
      .tp-card { background: var(--tp-surface); border: 1px solid var(--tp-border); border-radius: var(--tp-radius); }
      .tp-chip {
        display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.125rem 0.625rem;
        border-radius: 999px; background: var(--tp-surface-2); font-size: 0.875rem; font-weight: 600;
      }
      .tp-sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
    `,
  ],
})
export class PlannerThemeComponent {}
