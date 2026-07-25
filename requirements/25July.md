# LifeOS — Multi-module enhancements

Implement the following enhancements end-to-end (backend + frontend + tests where patterns already exist). Match existing LifeOS patterns: FastAPI modules under `backend/app/modules/`, Angular standalone components under `frontend/src/app/features/`, shared UI where possible. Do not invent new visual systems — reuse existing form/panel/detail patterns.

---

## 1. Goals — period types (weekly / monthly / yearly)

**Context:** Goals currently have `title`, `description`, `category`, `status`, `progress`, `notes`, `target_date`, milestones — but no period.

**Requirements:**
- Add a required (or defaulted) `period` field on goals: `weekly | monthly | yearly`| custom date as well (include `daily` only if it fits existing UX; otherwise stick to the three requested).
- Persist on model + Pydantic schemas + API create/update.
- Expose on frontend `goal.models.ts`, goal form (`<select>`), list, and detail.
- Optional but preferred: list filter/tabs by period (All / Weekly / Monthly / Yearly).
- `target_date` remains as the deadline within that period; do not remove it.
- Migrate existing goals: default period to `yearly` (or document chosen default) so nothing breaks.
- Add a separate section to keep all pending which missed which is defined in period.

**Files to touch (start here):**
- `backend/app/modules/goals/` (models, schemas, service, repository, api)
- `frontend/src/app/features/goals/`

---

## 2. Running — optional shoes + distance-by-shoe stats

**Context:** Runs have date, distance, duration, weather, location, notes — no shoes. Mirror the Q&A **optional type** pattern.

**Requirements:**
- Add a user-scoped shoe registry (like `QAType` / `/qa/types`):
  - Table e.g. `running_shoes` with `user_id`, `name`, unique per user.
  - API: list shoes, create shoe (and soft-delete/archive later if needed).
  - Suggested seed names optional (e.g. common shoe nicknames) — not required.
- On `Run`, add optional `shoe_id` (FK) or `shoe` name string consistent with Q&A’s optional `type`. Prefer FK + display name if you already use relational patterns; otherwise match Q&A’s string approach for consistency.
- Frontend run form: reuse shared `<app-type-select>` (or a thin shoes wrapper) — pick existing shoe, clear, or **+ Create "…"** calling create API. Field is optional; omit = no shoe.
- Within Running module, show stats: total km (and optionally #runs) **per shoe** (“How much has this shoe run?”). Surface on list/stats/detail in a natural place (shoe filter + per-shoe totals).
- Do not make shoes required for existing runs; backfill null.

**Pattern to copy:**
- Backend: `backend/app/modules/qa/` (`QAType`, types endpoints)
- Frontend: `frontend/src/app/shared/type-select/type-select.component.ts` + Q&A form usage

**Files:**
- `backend/app/modules/running/`
- `frontend/src/app/features/running/`

---

## 3. Integrations — Telegram card UX

**Context:** Integrations Telegram card always shows Bot Token + Chat ID. Only “How to integrate your bot” uses `<details>` fold. Token is `type="password"` (masked) but no eye toggle; Chat ID is plain text.

**Requirements:**
1. Make the credentials/config block **foldable** the same way as “How to integrate your bot” (`<details>` / `<summary>`). Collapsed by default so Bot Token / Chat ID are not visible until expanded. Keep status badge / connection summary visible outside the fold if useful.
2. Bot Token and Chat ID: keep masked by default; add an **eye button** to reveal/hide each field (password-input + toggle pattern). Apply consistently.
3. Prefer a small shared password/secret input component if Settings also needs the same eye toggle (see §5).

**Files:**
- `frontend/src/app/features/integrations/integrations-page.component.ts`

---

## 4. Routines — period window + skip days (New Routine)

**Context:** Routines have `days_of_week`, timezone, blocks — no date range, no exception dates.

**Requirements (New Routine / Edit form):**
1. **Period:** optional or required `start_date` + `end_date` (or `period_start` / `period_end`) so the routine only applies within that window. Outside the window, calendar/sync should not expand/generate blocks.
2. **Skip days:** allow excluding specific dates (e.g. trip days) even if that weekday is normally active. Store as a list of ISO dates (JSON array or related table). UI: date picker “Add skip day” + removable chips/list.
3. Keep existing weekday checkboxes for the weekly pattern.
4. Update calendar sync / materialization to respect period + skip dates.
5. Show period and skip days on detail view.

**Files:**
- `backend/app/modules/routines/`
- Calendar sync that expands routines (e.g. `backend/app/modules/calendar/sync_service.py` and related)
- `frontend/src/app/features/routines/routine-form.component.ts` (+ models, detail)

---

## 5. AI Assistant — fix chat input to bottom

**Context:** `AiChatPanelComponent` already uses flex column + scrollable messages + `shrink-0` input, but in practice the input scrolls away as the chat grows.

**Requirements:**
- Pin “Ask Anything” / composer to the **bottom of the visible chat viewport**.
- Only the message list scrolls; the input never leaves the viewport.
- Fix parent layout containment (`min-height: 0`, overflow, flex) on `/assistant` page and any shell/aside embeds that break sticky input.
- Verify desktop full page, shell aside, and mobile layouts.

**Files:**
- `frontend/src/app/features/assistant/assistant-page.component.ts`
- `frontend/src/app/features/dashboard/widgets/ai-chat-panel.component.ts`
- `frontend/src/app/shared/layout/app-shell.component.ts` (if aside embeds the panel)

---

## 6. Settings — password eye + Integrations section + nav Pin category

### 6a. Password eye toggles
- On change-password fields (current / new / confirm): add eye button to show/hide, same control as Telegram secrets.

**Files:** `frontend/src/app/features/settings/settings-change-password.component.ts` (+ shared input if created)

### 6b. Notifications → Integrations (dedupe Telegram)
**Decision to implement:**
- Settings currently has a thin “Telegram notifications” panel (`NotificationSettings`: chat id + enable) that duplicates Integrations’ richer Telegram config (token, chat, digest, events, webhook).
- **Rename** the Settings section from “Notifications” to **“Integrations”**.
- Remove the redundant Telegram credentials/chat-id form from Settings if Integrations already owns it.
- Make Settings → Integrations useful as a **central enable/disable entry point** for integrations (Telegram first; extensible): radio or toggle per integration (Enabled / Disabled) that turns that integration on/off without re-entering secrets. Secrets and advanced config stay on Integrations page.
- Keep `/notifications` inbox as-is (message inbox ≠ settings).

**Files:**
- `frontend/src/app/features/settings/settings-hub.component.ts`
- `frontend/src/app/features/settings/settings-notifications-section.component.ts` (rename/repurpose)
- Backend notifications vs integrations config — wire enable/disable to the real integration connection, avoid two sources of truth

### 6c. Sidebar: “Pin” category + DB-backed categories + within-category reorder
**Current behavior:** Categories (Core, Health, Growth, Knowledge, Insights, System) are hardcoded on `NAV_DESTINATIONS` in `nav-registry.ts`. Pins live in localStorage. Settings drag-reorder is a flat list across all pinned items — not constrained within category.

**Requirements:**
1. Add a top sidebar group **Pin** (or “Pinned”). When a module is pinned for “top pin,” it appears under Pin and is **removed from its normal category** in the sidebar until unpinned.
2. Persist **categories** and **module→category** mapping at **DB level** (per user or system defaults + user overrides) so future modules can be assigned categories without frontend-only hardcoding. Purpose if user reorder it will fetch and keep in user. Suppose i set reordering and pin some in web but in mobile again i need to set and then again in for ipad that i dont want.  Keep a sensible default seed matching today’s Core / Health / Growth / Knowledge / Insights / System + new **Pin** behavior.
3. Fix reorder: dragging a module in Settings/sidebar must **only reorder within its current category** (or within Pin when pinned). Do not allow cross-category drag via the reorder UX (category changes stay an explicit action if needed).
4. Update `nav-preferences` / app-shell `navGroups()` to:
   - Show Pin group first (if any pinned-to-top items)
   - Then other categories with remaining (non–top-pinned) items
5. Migration path: move from localStorage-only pins to API-backed preferences without wiping user pins if possible.

**Files:**
- `frontend/src/app/shared/layout/nav-registry.ts`
- `frontend/src/app/core/services/nav-preferences.service.ts`
- `frontend/src/app/shared/layout/app-shell.component.ts`
- `frontend/src/app/features/settings/settings-sidebar-section.component.ts`
- New backend module or settings endpoints for nav categories / pin order

---

## Implementation guidelines

- Prefer small shared UI for secret fields with eye toggle; reuse across Settings password + Integrations Telegram.
- Follow existing migration / Alembic patterns for schema changes.
- Add or extend tests where modules already have them (e.g. routines, goals, running).
- Keep changes scoped to the requirements above; no drive-by refactors.
- After each area: verify create/edit/list/detail and that calendar/sync (routines) and running stats still work.

## Acceptance checklist

- [ ] Goals can be created as weekly / monthly / yearly/ Custom; existing goals still load
- [ ] Runs can optionally pick/create a shoe; Running shows km per shoe
- [ ] Telegram card credentials are collapsed by default; eye toggles work for token + chat id
- [ ] Routines support start/end period and skip dates; those dates are honored in expansion/sync
- [ ] Assistant chat input stays fixed at bottom while messages scroll
- [ ] Settings passwords have eye toggles
- [ ] Settings “Notifications” renamed to “Integrations”; Telegram secrets not duplicated; enable/disable entry points exist
- [ ] Sidebar has Pin on top; pinned modules leave their category; categories stored in DB; reorder only within category
- [ ] Make sure mobile and all size of screen friendly also worked in both dark and light mode.
- [ ] Keep light and dark mode dynamic if its 6:00 AM to 7:PM IST make light mode and vice versa.