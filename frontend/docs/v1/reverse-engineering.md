# Reverse Engineering — Current State (v1)

## Overview
LifeOS is a "Personal AI Operating System" single-page application. The frontend is an
Angular 19 standalone-component app with an offline-first architecture.

## Technology Stack
- **Framework**: Angular 19 (standalone components, signals, new control flow `@if`/`@for`)
- **Styling**: Tailwind CSS 4 (`@tailwindcss/postcss`) + a small custom layer in `src/styles.css`
- **Offline storage**: Dexie (IndexedDB) with a `SyncService`
- **Validation**: Zod
- **PWA**: `@angular/service-worker` (`provideServiceWorker`, `ngsw-config.json`)
- **Build**: Angular CLI application builder

## Application Structure
- Bootstrap: `src/main.ts` → `AppComponent` → `app.config.ts` providers.
- Routing: `src/app/app.routes.ts` — lazy `loadComponent` routes, guarded by `authGuard`/`guestGuard`.
- Layout: `src/app/shared/layout/app-shell.component.ts` wraps all authenticated routes.
- Features (~28 modules under `src/app/features/`): dashboard, goals, tasks, habits, running,
  calendar, journal, mood, communication, qa, wishlist, notifications, export, files, learning,
  career, finance, analytics, timeline, reports, memory, coaches, ocr, voice, integrations,
  automations, predictions, life-timeline, profile, auth, search.

## UI / Responsiveness Findings
- **Theme**: Windows XP retro aesthetic driven by CSS variables (`--xp-blue`, `--xp-silver`,
  `--xp-panel`, `--xp-border`, ...) and utility classes (`.title-bar`, `.panel`, `.btn-primary`,
  `.input-field`). Feature templates reference these via Tailwind arbitrary values
  (e.g. `bg-[var(--xp-blue)]`).
- **Primary mobile blocker**: `app-shell.component.ts` renders a fixed `w-56` sidebar that is
  always visible with ~28 vertical links. No hamburger, drawer, or bottom navigation. On small
  screens the sidebar consumes most of the viewport.
- Dashboard grid is already responsive (`grid-cols-1 md:grid-cols-2 xl:grid-cols-3`).
- Some forms use fixed `grid-cols-2` (e.g. `task-form.component.ts`) which is cramped on phones.
- AI side panel is already gated to `lg+`.

## PWA Findings
- `manifest.webmanifest` declares only a single SVG icon (`sizes: "any"`); missing dedicated
  PNG icons (192/512), a dedicated maskable icon, and an apple-touch-icon.
- `index.html` lacks `viewport-fit=cover`, apple-touch-icon link, and `apple-mobile-web-app-*`
  meta tags; no `color-scheme` meta.
- `ngsw-config.json` defines only asset groups; no `dataGroups` (API/runtime caching) and no
  `navigationUrls`.
- No install prompt handling (`beforeinstallprompt`) and no update-available prompt (`SwUpdate`).
- No offline fallback screen.

## Conclusion
The foundation (Angular PWA + Tailwind + offline storage) is solid. The gaps are concentrated in
(1) the non-responsive shell/navigation, (2) an aesthetic that is not touch-optimized, and
(3) incomplete PWA installability/offline configuration.
