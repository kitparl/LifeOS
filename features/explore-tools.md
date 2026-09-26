# Feature: Explore Tools (guest access)

Visitors can use a set of free LifeOS tools without an account. The login page has an **Explore free tools** button that opens a public shell with the same look and layout as the app (sidebar, header, mobile drawer and bottom nav). The free tools are **Developer** and **News**.

Developer is frontend only. News calls the public live-news endpoints (see [News for guests](#news-for-guests)); nothing a guest does creates a database row.

---

## Routes

| URL | What it shows |
|-----|---------------|
| `/explore` | The tool list page (a card for each free tool) |
| `/explore/developer` | The Developer dashboard |
| `/explore/developer/<tool>` | A Developer tool, e.g. `/explore/developer/base64` |
| `/explore/news` | The News hub (Latest, Categories, Search; Saved and Collections are locked) |
| `/explore/news/article?url=…` | News article details |
| `/explore/news/collections/<id>` | Redirects to `/explore/news?tab=collections` (locked) |
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

Only add tools that work fully client-side, or whose backend calls are public. Never add a private module. A tool with account-only parts (like News) must lock those parts for guests, not hide or call them.

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

---

## News for guests

News routes live in `features/news/news.routes.ts` (`NEWS_ROUTES`) and are mounted at `/news` (app shell) and `/explore/news` (guest shell), like Developer. Back links are relative (`..`, `../..`). Article cards and rows render at different route depths (hub and collection page), so they build their link from `newsRootPath(mode)`.

**Access mode.** `NEWS_ACCESS_MODE` (`features/news/news-access-mode.ts`) defaults to `'user'`. The explore mount sets `'guest'` through `NEWS_GUEST_PROVIDERS`. Components read the token; nothing sniffs the URL.

| Surface | Signed in | Guest |
|---------|-----------|-------|
| Latest, Categories, Search, article details | Live news with saved stars | Same, `saved_article_id` always `null` |
| Save star | Saves / unsaves, then offers "Add to collection?" | Locked star; click opens "Sign in to save articles" + **Sign in** |
| Saved and Collections tabs | The user's library | Tab stays visible; shows "Not available for free users" + **Sign in**; loads nothing |
| `/news/collections/:id` | Collection page | `newsAccountGuard` redirects to the locked Collections tab |

Sign in links go to plain `/login` (the login page has no return-URL support yet). Guests are never auto-redirected to login.

**Shared locked UI** (`shared/guest-locked/`), reusable by any future free tool:

- `GuestLockedControlComponent`: keeps the projected trigger visible with `aria-disabled`, opens a small popover (`.menu` styles) on click with a message and **Sign in**. Closes on Escape (focus returns to the trigger) or an outside click. Works on touch.
- `GuestLockedPanelComponent`: an `.empty-state` with a title, message, and **Sign in**.

**Backend.** `GET /news/categories`, `/news/articles` and `/news/article` use `get_optional_user` (`app/core/deps.py`): no token means anonymous, and a bad token is still a 401. Anonymous callers get no saved-state lookup. The FreeNewsAPI proxy limit (`news_proxy_per_minute`) is per user when signed in and per client IP (hashed, `guest:<sha256>`) when anonymous; see `proxy_limit_key` in `app/modules/news/rate_limit.py`. Saved-article and collection routes still require `get_current_user`.
