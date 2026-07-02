# Requirements — Responsive + Best-in-Class PWA (v1)

## Goal
Make the LifeOS frontend fully responsive/mobile-first and an installable, offline-capable,
best-in-class Progressive Web App.

## Functional Requirements

### FR-1 Responsive Navigation
- FR-1.1: On phones (< `lg`), the primary navigation MUST NOT occupy persistent horizontal space.
- FR-1.2: Provide a top app bar with a menu button that opens a slide-in drawer containing the
  full, grouped navigation.
- FR-1.3: Provide a bottom tab bar on mobile with the most-used destinations plus a "More" entry.
- FR-1.4: On desktop (`lg+`), retain a left sidebar; allow it to collapse.
- FR-1.5: Navigating MUST close the mobile drawer; body scroll MUST lock while the drawer is open.

### FR-2 Responsive Content
- FR-2.1: Multi-column form/detail grids MUST collapse to a single column on small screens.
- FR-2.2: Interactive targets MUST be at least 44x44 CSS px.
- FR-2.3: Layout MUST respect device safe-area insets (notches / home indicator).

### FR-3 Theming
- FR-3.1: Provide a modern, clean design system via CSS variables.
- FR-3.2: Support light and dark modes (system preference + manual toggle persisted locally).

### FR-4 PWA Installability
- FR-4.1: Provide PNG icons at 192 and 512, a maskable icon, and a 180px apple-touch-icon.
- FR-4.2: Manifest MUST include `id`, icons, app `shortcuts`, `categories`, and display mode.
- FR-4.3: `index.html` MUST include iOS web-app meta and `viewport-fit=cover`.
- FR-4.4: Offer a custom install affordance driven by `beforeinstallprompt`.

### FR-5 PWA Offline + Updates
- FR-5.1: Cache API GET responses and static assets via service-worker `dataGroups`.
- FR-5.2: Notify the user when a new app version is available and allow reload to update.
- FR-5.3: Show an offline fallback screen when a navigation fails while offline.

## Non-Functional Requirements
- NFR-1 (Compatibility): Preserve existing utility class names (`.panel`, `.btn-primary`,
  `.input-field`, `.title-bar`) and CSS variable names so existing feature templates keep working
  without per-file edits.
- NFR-2 (Performance): Stay within existing production budgets (initial < 1MB error / 500kB warn).
- NFR-3 (Accessibility): Drawer/toggles keyboard-operable with appropriate ARIA; visible focus.
- NFR-4 (No regressions): Existing routes, auth flow, and sync behavior remain intact.

## Out of Scope (v1)
- Full per-feature mobile audit of all ~28 modules (candidate for v2).
- Web push notifications.
