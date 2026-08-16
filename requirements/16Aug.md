# LifeOS — Requirements (16 Aug 2026)

**Date:** 16 Aug 2026
**Owner:** Pranshu Bisht
**Capture mode:** Incremental — items added one by one until capture is closed.

Implement the following enhancements end-to-end (backend + frontend + tests where patterns already exist). Match existing LifeOS patterns: FastAPI modules under `backend/app/modules/`, Angular standalone components under `frontend/src/app/features/`, shared UI where possible. Do not invent new visual systems — reuse existing form/panel/detail patterns.

---

## 1. Running — default tab, Shoes Stats / Running Stats submodules, Personal Bests source links, Previous Runs delete

**Context:** Running page tabs are Previous Runs (default), Events & Competitions, Personal Bests, Goals. A “Distance by shoe” table sits above the tabs. Personal Bests currently use logged runs only (date column, no source link). Previous Runs shows mixed log-runs and events; actions are Edit only. Events can already be deleted from Events & Competitions.

**Requirements:**

### 1.1 Default tab
- Opening Running should default to **Events & Competitions** (not Previous Runs).
- Keep `?tab=` query-param override working for the other tabs.

### 1.2 New submodules beside Goals
Add two new tabs next to Goals (same tab strip):

1. **Shoes Stats**
   - Move the existing “Distance by shoe” information here (km, run count, last run — same data as today’s table).
   - **Remove** the “Distance by shoe” panel from the Running page above the tabs. Do not duplicate it.

2. **Running Stats**
   - Graphical / analysis view of running stats (charts). Reuse existing LifeOS chart/panel patterns if any exist; otherwise a simple chart set (e.g. distance over time, weekly totals) is enough — do not invent a new visual system.

Tab order suggestion: Previous Runs | Events & Competitions | Personal Bests | Goals | Shoes Stats | Running Stats (or place the two new ones immediately beside Goals as requested).

### 1.3 Personal Bests
- Personal Bests must consider **both log runs and events/competitions** (best pace/time for each distance bucket from either source).
- Add a new UI column **beside Date**:
  - If the PB came from an **event**: show the event name, linking (`href` / `routerLink`) to that event’s detail.
  - If the PB came from a **log run**: show a label/link to that run’s detail (same idea — clickable source).
- Date remains; the new column identifies the source and is navigable.

### 1.4 Previous Runs — delete actions
- Actions column currently has **Edit** only. Add **Delete**.
- **Log runs:** Delete is allowed from Previous Runs (and should work).
- **Events:** Do **not** allow delete from Previous Runs. Events may be deleted **only** from Events & Competitions. Show Edit for events in Previous Runs; omit Delete (or disable with no delete path).
- **Confirmation before every delete:**
  - **Web:** confirmation popup (modal), not a silent delete.
  - **Mobile:** use the platform confirmation pattern (native/mobile-app confirm dialog), consistent with how confirmations work in the mobile app.

**Files to touch (start here):**
- `frontend/src/app/features/running/running-list.component.ts` (tabs, default, shoes panel, PB columns, delete)
- `frontend/src/app/features/running/models/running.models.ts`
- `backend/app/modules/running/` (personal bests must include race events; PB payload needs source + name + ids for links)
- Existing delete APIs: `DELETE /runs/{id}` (log run only from this list); race delete stays on Events & Competitions

---

## 2. Routines — list order, delete, Active-only filter, period expiry cron, required start date, form UX

**Context:** Routines list is ordered by name; actions are Edit only (delete exists on detail). “Active only” checkbox defaults **unchecked**. `is_active` is already stored on `routines`. Period start/end are both optional; missing start lets calendar expansion fill **past** dates (bug). New Routine form is one card: details + four prefilled time blocks (DSA / Gym / Communication / Book). Area and Calendar category are native `<select>` enums.

**Requirements:**

### 2.1 List sort
- Routines list must be in **decreasing order by period** (latest `start_date` first, then `end_date`; routines with no end still sort by start).

### 2.2 List delete
- Actions currently have **Edit** only. Add **Delete** on the list.
- Confirmation: same as §1.4 — web confirmation popup; mobile native/app confirm.

### 2.3 “Active only” filter
- Checkbox **Active only** must be **checked by default** (list shows active routines only).
- Unchecking it shows **all** routines (active and inactive/paused). Do not require an extra Refresh click if a live toggle fits existing filter patterns; otherwise keep Refresh but default checked.

### 2.4 Auto-inactive when period is in the past
- `is_active` is already in the DB — use it.
- If period bounds put the routine **outside today** (period is in the past: `end_date` set and `end_date < today`; or both start and end set and today is not in `[start_date, end_date]`), mark **`is_active = false`**.
- Add a **cron in the existing APScheduler style** (`backend/app/modules/integrations/scheduler.py`) that runs **every day at 12:01 AM** and flips those expired routines to inactive. Also apply the same rule on create/update so already-expired periods are not saved as active.

### 2.5 Period start required
- **Period start is compulsory** (no longer optional). Period end stays optional.
- Reason: without a start date, calendar expansion fills historical dates with routine blocks (bug). Start date is the lower bound; do not materialize blocks before it.
- Enforce in UI (required date) and API/schema.

### 2.6 Default time blocks
- Do **not** open four prefilled blocks (DSA, Gym, Communication, Book) with titles/times filled.
- New Routine: **one empty block** by default. User adds further blocks with **+ Block**.

### 2.7 Form layout — Details vs Time blocks
- One card mixing “New Routine” details and time blocks is confusing.
- Split visually: a clear **Details** section (name, description, timezone, period, skip days, active days) and a distinct **Time blocks** section (identifier, spacing, or separate panel). Reuse existing panel/title-bar patterns; keep the page optimized, not a new design system.

### 2.8 Area & Calendar category — type-select
- Replace native `<select>` on **Area** and **Calendar category** with `<app-type-select>` (same flexible pick-or-create as Q&A Type). Existing values remain options; user can create a new one. Persist reusable values in the existing type-select / taxonomy pattern.

**Files to touch (start here):**
- `frontend/src/app/features/routines/routines-list.component.ts`
- `frontend/src/app/features/routines/routine-form.component.ts`
- `frontend/src/app/shared/type-select/type-select.component.ts` (reuse)
- `backend/app/modules/routines/` (sort, `start_date` required, expiry, delete on list uses existing delete API)
- `backend/app/modules/integrations/scheduler.py` (12:01 AM job)

---

## 3. Habits — list delete with confirmation

**Context:** Habits list actions are **Edit** only. Delete already exists on habit detail (`confirm('Delete this habit permanently?')`) and `DELETE` API. Same gap as Running Previous Runs and Routines list.

**Requirements:**
- Add **Delete** next to Edit on the Habits list actions column.
- **Reconfirm before every delete** (and any other destructive action in this module — list, detail, or elsewhere delete is offered). Do not delete silently.
- Confirmation UX: same as §1.4 — **web** confirmation popup; **mobile** native/app confirm dialog.

**Files to touch (start here):**
- `frontend/src/app/features/habits/habits-list.component.ts`
- Existing `habits.service.ts` `delete()` / habit detail delete path (reuse; upgrade confirm to popup/native if still using `window.confirm`)

---
