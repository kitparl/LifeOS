# Feature: Explore Tools (guest access)

Visitors can use a set of free LifeOS tools without an account. The login page has an **Explore free tools** button that opens a public shell with the same look and layout as the app (sidebar, header, mobile drawer and bottom nav). The only tool so far is **Developer**.

This is frontend only. No backend, API, or database is involved.

---

## Routes

| URL | What it shows |
|-----|---------------|
| `/explore` | The tool list page (a card for each free tool) |
| `/explore/developer` | The Developer dashboard |
| `/explore/developer/<tool>` | A Developer tool, e.g. `/explore/developer/base64` |
| `/explore/<unknown>` | Redirects to `/explore` |

- **Logged-in users** who open any `/explore/**` URL are redirected to the same page inside the app, keeping the sub-path, query string, and fragment. For example, `/explore/developer/base64` goes to `/developer/base64`. `/explore` itself goes to `/`. The redirect is `exploreGuard` in `frontend/src/app/features/explore/explore.guard.ts`.
- **Logged-out visitors** can deep-link to and refresh any `/explore/**` URL. `AuthService.clearSession()` treats `/explore/**` as public, so a failed token refresh never bounces a visitor to `/login`.
- `guestGuard` (logged-out only, used by login and register) is **not** used here.

---

## What guests get, and what they don't

| Included | Not included |
|----------|--------------|
| LifeOS brand, free-tool nav, page title, theme toggle | AI Assistant (panel, mobile sheet, AI tab, `/assistant`) |
| Desktop sidebar (collapse / hide) and header | Notifications (bell and `/notifications`) |
| Mobile drawer and bottom nav (tools · **Sign in** · **More**) | Word of the Day, sync status chip |
| **Sign in** (links to `/login`) | Command palette (⌘K), nav pinning |
| | Log out, PWA install banner, every private module |

The guest shell is `GuestShellComponent` (`features/explore/guest-shell.component.ts`). It injects only `Router` and `ThemeService`. It shares its nav styles with `AppShellComponent` through `shared/layout/shell-nav.css`.

---

## Adding a free tool

Add **one entry** to `EXPLORE_TOOLS` in `frontend/src/app/features/explore/explore-tools.registry.ts`:

```ts
{
  id: 'my-tool',
  label: 'My Tool',
  description: 'One line shown on the tool list card.',
  icon: 'wrench',                 // Lucide name; register it in shared/layout/nav-lucide.ts if new
  path: 'my-tool',                // -> /explore/my-tool
  authRoute: '/my-tool',          // where logged-in users are redirected
  providers: [],                  // optional route-level providers (e.g. guest-scoped storage)
  loadChildren: () => import('../my-tool/my-tool.routes').then((m) => m.MY_TOOL_ROUTES),
}
```

The sidebar, drawer, bottom nav (first 3 tools), tool list page, header title, and logged-in redirect all read from this registry. You don't need to change the shell.

Only add tools that work fully client-side, or whose backend calls are public. Never add a private module.

---

## Developer tools under two prefixes

The Developer routes live in one place, `features/developer/developer.routes.ts` (`DEVELOPER_ROUTES`), and are mounted twice:

- `/developer`: inside the authenticated `AppShellComponent`, unchanged for logged-in users.
- `/explore/developer`: inside `GuestShellComponent`.

Links inside the Developer feature are **relative** (dashboard **Open** → `[tool.route]`, tool back link → `..`), so they work under either prefix. Keep new links relative.

---

## Storage (favorites and history)

Logging out does not clear browser storage. So that someone using the owner's browser after logout can't see the owner's tool activity, guests get their own storage:

| Data | Logged-in | Guest (`/explore/developer`) |
|------|-----------|------------------------------|
| Favorites (localStorage) | `lifeos-dev-tools-favorites` | `lifeos-dev-tools-favorites-guest` |
| History (IndexedDB) | `DevToolsHistoryDB` | `DevToolsHistoryDB-guest` |
| Sidebar collapsed / hidden | `lifeos-sidebar-collapsed` / `-hidden` | `lifeos-guest-sidebar-collapsed` / `-hidden` |

How the scoping works:

- `DEV_TOOLS_STORAGE_SCOPE` (`features/developer/shared/dev-storage-scope.ts`) defaults to `'user'`.
- The explore route sets `'guest'` through `DEVELOPER_GUEST_PROVIDERS`, which also creates guest-only instances of `DevFavoritesService` and `DevHistoryService`.
- The logged-in keys are unchanged, so no migration is needed.
