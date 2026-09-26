# Code Quality Guide

How LifeOS code is organised, why, and how to keep it that way. This came out of the September 2026 production cleanup (branch `chore/code-cleanup`). The change-by-change record lives in the commit history.

## 1. Principles applied

- **Behaviour first.** Cleanups never change API contracts, the DB schema, auth, env var names, or the UI. The backend's OpenAPI document and route table were diffed against a snapshot after every step.
- **Layering.** Backend: `api.py` (HTTP) → `service.py` (rules) → `repository.py` (SQLAlchemy) → `models.py`, with `schemas.py` for request/response shapes. Routes don't query the DB; repositories don't raise HTTP errors.
- **Errors.** Services raise the `AppError` family from `app/core/exceptions.py` (`NotFoundError`, `ConflictError`, `TooManyRequestsError`, `PayloadTooLargeError`, …) and use `get_or_404`. `main.py` maps them to `{"detail": ...}`, the same shape as FastAPI's `HTTPException`. Use `HTTPException` only at the HTTP boundary when a response header is needed (e.g. 416 with `Content-Range`).
- **Logging.** Never `print`. Never swallow an exception silently: if a failure is tolerable, log it (`logger.warning(..., exc_info=True)`) and say why in a comment. Never log secrets, tokens, or `.env` values; user IDs and counts are fine.
- **Time.** All timestamps are stored in UTC. Naive values from SQLite are treated as UTC.
- **Frontend.** `HttpClient` appears only in `*.service.ts`; request configuration lives in the interceptors. Components get data from feature services.
- **Dead code** is deleted, not commented out. "Unused" is checked across code, templates, routes, barrels, lazy imports, and tests before deleting.

## 2. Key decisions and why

- **Shared helpers went into `core/` only when duplicated.** For example, there were 4 hand-rolled rate limiters, 6 "suggested + user names" merge loops, 3 purge loops, 15 `X-Total-Count` mappings, and 3 `formatSize` copies. Single-use logic stayed where it was.
- **UTC vs local "today" was kept per call site.** The frontend helpers are named `utcIsoDate` / `localIsoDate` so the difference is visible. Several forms default to the *UTC* date, which is yesterday between 00:00 and 05:30 IST. That was flagged rather than silently changed, because it's user-visible.
- **Angular's `HttpStatusCode` over a custom constants file.** The framework already ships it. It costs about 2.7 kB in the initial bundle.
- **`apiErrorMessage` is used for API error text.** It reads string details, `{code, message}` details, and 422 lists. The exceptions are sites that branch on error codes or join all validation messages; they keep their own handling.
- **Splits only at clear seams.** For example, the calendar's event modal and the knowledge-notes view state. Components whose state is shared with the parent (the task People panel, the calendar quick-create modal) were left alone rather than rewired.
- **Kept but unused-looking:**
  - The `digest_*` Telegram preference fields: they're part of stored config and the API response.
  - `clear_all_for_tests` / `reset_vendor_state`: test hooks.
  - Backend packages with no direct import (uvicorn, DB drivers, email-validator, python-multipart, tzdata): used indirectly.
- **Removed together with its tests:** code that only tests exercised (the legacy digest path, `EditorPersistenceService`), after explicit sign-off.
- **`backend/db-recovery/` is ignored and untracked**, because it held a dev-database dump. It still exists in git history; see the final report for the purge procedure.

## 3. Shared locations

| Location | What lives there | Why there |
|---|---|---|
| `backend/app/core/timezone.py` | `utc_now`, `utc_today`, `as_utc`, `start_of_day_utc`, `ist_now`, `ist_today`, `safe_zone` | One definition of "now" and of naive-timestamp handling; also the ORM default for timestamps |
| `backend/app/core/database.py` | `new_id` (UUID primary keys) | Every model's id default |
| `backend/app/core/rate_limit.py` | `SlidingWindowLimiter` | Auth, task assignments, and the news proxy all need per-key limits |
| `backend/app/core/cache.py` | `TtlCache` | News and analytics caches |
| `backend/app/core/taxonomy.py` / `retention.py` | Name registries; soft-delete purge | Used by 5 and 3 modules respectively |
| `backend/app/core/security.py` | Tokens, hashing, `cookie_kwargs` | All auth cookie attributes in one place |
| `backend/app/modules/integrations/common.py` | `load_json_object`, `mask_secret`, `last_test_ok` | Shared by the AI, Wordnik, GitHub, Google, and Telegram configs |
| `backend/app/modules/tasks/due_dates.py` | `noon_utc`, `resolve_due_token` | Due-date tokens for AI quick-add and Telegram |
| `frontend/src/app/core/utils/date.ts` | `utcIsoDate`, `localIsoDate`, `toDatetimeLocalValue`, `yearMonthKey`, `pad2` | Date-input and key formatting |
| `frontend/src/app/core/utils/http.ts` | `Page<T>`, `toPage`, `apiErrorMessage` | List endpoints and API error text |
| `frontend/src/app/core/utils/format.ts` | `formatBytes` | File sizes |
| `frontend/src/app/core/services/preferences-api.service.ts` | `/preferences/{key}` GET/PUT | Used by the 4 preference services |

## 4. Conventions going forward

**Backend**
- Code must run on **Python 3.10** (production). Ruff's `target-version = "py310"` keeps pyupgrade from emitting 3.11+ code, but it doesn't know stdlib APIs: don't use `datetime.UTC` (use `timezone.utc`), `typing.Self` (use `typing_extensions`), `StrEnum`, `tomllib`, `asyncio.TaskGroup`, or 3.11 `fromisoformat` formats.
- Never call `datetime.now(...)` or `ZoneInfo(...)` inline. Use `app.core.timezone`.
- Model ids use `default=new_id`; timestamps use `default=utc_now` (and `onupdate=utc_now`).
- For a missing row, `get_or_404(await repo.get(...), "X not found")`.
- For per-key throttling, use `SlidingWindowLimiter` + `TooManyRequestsError`. Don't write another limiter.
- Status codes come from `fastapi.status` (API) or `httpx.codes` (outbound clients), never bare numbers.
- A new model module must be registered in `schema_bootstrap._import_models()`, or fresh deploys will miss its tables.

**Frontend**
- List endpoints: `observe: 'response'` + `map(toPage)`, returning `Page<T>`.
- Show API errors with `apiErrorMessage(err, 'Fallback text')`.
- Status checks use `HttpStatusCode.*`.
- Date inputs use `localIsoDate`/`toDatetimeLocalValue`; use `utcIsoDate` only when you mean the UTC calendar.
- Don't name `@Output()`s after DOM events (`close`, `toggle`, `click`, …).
- No `console.log` in app code.

**Gates, all expected to pass before a merge:**

```bash
cd backend  && pytest -q && ruff check app
cd frontend && npm run lint && npm run test:ci && npm run build
```

## 5. Before/after ratings

| Area | Before | After | Why |
|---|---|---|---|
| Backend | 6/10 | 8/10 | **Before:** sound layering, but 398 lint findings, duplicated helpers (limiters, caches, time, taxonomy), a deploy bootstrap that skipped 21 tables, dead and legacy code. **After:** lint clean, one shared helper per concern, the bootstrap fixed, contract identical. Not higher because of in-process rate limits, hand-rolled migrations, and still-large services (`github/sync_service`). |
| Frontend | 6/10 | 7.5/10 | **Before:** 1 lint error + 32 warnings, a flaky spec, duplicated date/list/error code, dead components. **After:** lint 0/0, shared utils, dead code gone, the QA flake fixed at its cause. Not higher because of one unreproduced 4-failure Karma run, large components (`knowledge-subject`, 1,287 lines), an initial bundle over budget, and the UTC "today" defaults. |
| Overall | 5.5/10 | 7.5/10 | **Before:** a dev-DB dump was tracked in git, the docs linked to deleted files and described removed modules, and the lint command was stale. **After:** the dump is untracked and ignored, the docs match the code, and the quality gates are documented. Not higher because the dump is still in git history until purged, and there is no CI enforcing the gates. |
