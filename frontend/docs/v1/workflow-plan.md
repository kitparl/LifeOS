# Workflow Plan (v1)

## Phase decisions (AI-DLC adaptive)
- **Workspace Detection**: DONE — brownfield Angular 19 PWA.
- **Reverse Engineering**: DONE — see `reverse-engineering.md`.
- **Requirements Analysis**: DONE — see `requirements.md` (standard depth).
- **User Stories**: SKIPPED — single-user personal app; requirements capture intent sufficiently.
- **Workflow Planning**: this document.
- **Application Design**: DONE — see `application-design.md`.
- **Units Generation**: SKIPPED — single cohesive frontend unit.
- **Construction**: single unit "frontend-responsive-pwa"; Code Generation + Build.

## Execution order (maps to plan to-dos)
1. AI-DLC docs (this folder).
2. Design-system foundation — `styles.css` tokens, dark mode, safe-area, touch targets.
3. Responsive app shell — sidebar/drawer/bottom-nav, grouped nav, theme toggle.
4. Key-screen responsive patterns — dashboard + tasks.
5. PWA hardening — icons, manifest, index.html meta, ngsw-config, PwaService, offline fallback.
6. Verify — production build; fix introduced errors.

## Risks & mitigations
- **Broad template dependency on `--xp-*` variables** → keep variable + class names as aliases; no
  mass template rewrites.
- **Production budgets** (`anyComponentStyle` 4kB warn / 8kB error) → keep component-inline styles
  minimal; put shared styles in global `styles.css`.
- **Service worker only active in production build** → verify via `npm run build`.

## Definition of done
- Mobile shell usable (drawer + bottom nav), desktop sidebar collapsible.
- Light/dark theme with persistence.
- Installable PWA with valid icons/manifest, offline caching, update + install prompts, offline page.
- `npm run build` succeeds within budgets.
