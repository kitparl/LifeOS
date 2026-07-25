# LifeOS Scheduled Reports & Reminders

Engineering and product guide for the **scheduler-driven Telegram reports** feature: morning / midday / night / weekly / AI briefing jobs, birthday & immutable event reminder ladders, routine lead-time reminders, and the `scheduled_report_runs` audit log.

Related docs:

- [TELEGRAM_BOT_GUIDE.md](./TELEGRAM_BOT_GUIDE.md) — end-user bot UX
- [TELEGRAM_NOTIFIER.md](./TELEGRAM_NOTIFIER.md) — notifier registry, outbox, encryption

---

## Mission

Deliver reliable, **self-contained text reports and reminders** to Telegram for users who have an **enabled** Telegram `integration_connections` row.

- Prefer extending DigestService, APScheduler, calendar recurrence, and routines — not a second scheduling product.
- Business logic stays in domain modules; Telegram only formats and sends via the Notifier registry.
- Default timezone for product defaults: **`Asia/Kolkata` (IST)**.

---

## Day shape (IST defaults)

```text
06:00     Morning report
08:00     AI briefing (optional, off by default)
12:30     Midday nudge (skip if empty)
22:00     Night wrap
Sun 18:00 Weekly review
*/10 min  Reminder poller (birthdays, immutable events, routine blocks)
```

Prefs store local clock times; cron triggers use the user’s timezone (default IST).

---

## Who gets jobs

Every scheduled job **must**:

1. Resolve `IntegrationConnection` where `provider == "telegram"` and `enabled == true`.
2. If missing or disabled → **do not send**; log the run as `skipped` / `telegram_disabled`.
3. Respect per-job prefs toggles (morning / midday / night / weekly / AI / reminder toggles).
4. On API startup, register jobs only for `list_enabled_telegram()`. On prefs save or Telegram disable → sync / remove jobs.

---

## Cron suite

| Job type | APScheduler id | Default (IST) | Frequency | Skip if empty? |
|----------|----------------|---------------|-----------|----------------|
| `morning` | `telegram_morning_{user_id}` | 06:00 | Daily | No (send “all clear”) |
| `ai_briefing` | `telegram_ai_briefing_{user_id}` | 08:00 | Daily (optional) | Yes / off / no API key |
| `midday` | `telegram_midday_{user_id}` | 12:30 | Daily | Yes |
| `night` | `telegram_night_{user_id}` | 22:00 | Daily | No |
| `weekly` | `telegram_weekly_{user_id}` | Sun 18:00 | Weekly | No |
| Reminder poll | `telegram_reminder_poll` (shared) | every 10 min | Interval | Yes (most ticks no-op) |

Implementation: [backend/app/modules/integrations/scheduler.py](../backend/app/modules/integrations/scheduler.py).

---

## Report contents (text only)

Messages are HTML (`parse_mode=HTML`). Long bodies are split with `chunk_text` (~3900 chars) into Part 1 / Part 2.

### Morning (06:00)

1. **Routine today** — `RoutineService.today_preview` (honours `skip_dates`)
2. **Pending tasks** — Overdue / Due today / Later (capped + “+N more”)
3. **Calendar** — today → +7 days (includes expanded yearly birthdays / immutable events and routine blocks)
4. **Habits open** — not completed today + streak when available; may mention habits linked to today’s blocks
5. **Goals** — short active list with progress %

### Midday (12:30)

Overdue + due-today tasks only. **Skip send if none.**

### Night (22:00)

- Tasks completed today (count + short list)
- Habits still open
- **Tomorrow:** routine preview + calendar + tasks due tomorrow

### Weekly (Sunday 18:00)

- Goal progress summary
- Habit streak highlights
- Next 7 days calendar (including birthdays)

### AI briefing (08:00, optional)

Separate job calling existing report/AI helpers. Must not block morning.

Builders: [report_builders.py](../backend/app/modules/integrations/report_builders.py).  
Orchestration + audit: [scheduled_report_service.py](../backend/app/modules/integrations/scheduled_report_service.py).  
Templates: [telegram_templates.py](../backend/app/modules/integrations/telegram_templates.py).

`POST /api/v1/integrations/telegram/digest` and “Send morning now” both run the enriched **morning** report (`DigestService` → `ScheduledReportService.run(..., "morning")`).

---

## Preferences

Stored as plaintext JSON fields alongside encrypted secrets in `integration_connections.config_json`.

| Pref | Default |
|------|---------|
| `timezone` | `Asia/Kolkata` |
| `morning_enabled` / `morning_time` | true / `06:00` |
| `midday_enabled` / `midday_time` | true / `12:30` |
| `night_enabled` / `night_time` | true / `22:00` |
| `weekly_enabled` / `weekly_time` / `weekly_weekday` | true / `18:00` / Sunday (`6`) |
| `ai_briefing_enabled` / `ai_briefing_time` | false / `08:00` |
| `birthday_reminders_enabled` | true |
| `immutable_reminders_enabled` | true |
| `routine_reminders_enabled` | true |

**Backward compatibility:** if `morning_*` keys are absent, they fall back to legacy `digest_enabled` / `digest_time`. Saving morning prefs also mirrors into `digest_*` so older clients keep working.

UI: **Settings → Integrations → Telegram → Scheduled reports**.

---

## Calendar: yearly + event kind

### Yearly recurrence

`EVENT_RECURRENCE` includes `yearly`. Expansion in `CalendarService._expand_recurring_event` repeats the same month/day each year.

- **Feb 29:** in non-leap years occurrences land on **Feb 28**.
- One master event row; no cloning a new row each year.

### Event kind

Additive column `event_kind`: `normal` | `birthday` | `immutable` (default `normal`).

| Kind | Meaning |
|------|---------|
| `normal` | Ordinary event; no special reminder ladder |
| `birthday` | Forces `recurrence=yearly`; uses **birthday** reminder ladder |
| `immutable` | Non-changeable reminder policy; uses **immutable** ladder |

Create/edit in the Calendar UI (**Event kind** select). Birthday implies yearly automatically.

---

## Reminder ladders

Shared job `telegram_reminder_poll` runs every **10 minutes**, scans enabled Telegram users, and sends at most once per `(user, occurrence, offset)` via unique `dedupe_key`.

### Birthdays

Offsets relative to birthday **local date**:

| When | Offset |
|------|--------|
| 2 days before | T−2 (any poll that calendar day; deduped) |
| 1 day before | T−1 |
| On birthday | **11:55** local on the birthday date |

Example: `🎂 Birthday tomorrow: Alice` / `🎂 Today: Alice`.

### Immutable events

Before event start: **7d, 3d, 1d, 6h, 1h, 59m**.

### Routine blocks

Before `start_time` for today’s / near-term expanded blocks: **30m, 15m, 5m, 1m**.  
Honours `skip_dates` (no reminders that day).

Dedupe key examples:

- `bday:{event_id}:{occurrence_date}:tminus1`
- `imm:{event_id}:{occurrence_iso}:59m`
- `routine:{routine_id}:{HHmm}:{date}:5m`  
  (block start time, not block id — routine updates recreate block rows)

Implementation: [reminder_scanner.py](../backend/app/modules/integrations/reminder_scanner.py).

---

## Habits inside routines

Join table `routine_block_habits` (`block_id`, `habit_id`) — many habits per block.

- Create/edit routine blocks → multi-select existing habits.
- Morning / night reports may mention habits linked to today’s blocks.
- Completing a habit stays on `HabitService` (no auto-complete when a block’s time passes).

---

## Audit table: `scheduled_report_runs`

Every cron / reminder attempt is persisted.

| Column | Notes |
|--------|--------|
| `job_type` | `morning`, `midday`, `night`, `weekly`, `ai_briefing`, `birthday_reminder`, `immutable_reminder`, `routine_reminder`, … |
| `status` | `started`, `sent`, `skipped`, `failed` |
| `skip_reason` | `telegram_disabled`, `prefs_off`, `empty`, `duplicate`, … |
| `dedupe_key` | Unique when set — reminder idempotency |
| `sections_json` | Counts / meta |
| `message_chars` | Length of sent text |
| `started_at` / `finished_at` | Timing |

Indexes: `(user_id, job_type, created_at)`, `(status, created_at)`, unique on `dedupe_key`.

Model: [report_models.py](../backend/app/modules/integrations/report_models.py).

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| `PUT` | `/api/v1/integrations/telegram/config` | Save prefs (+ secrets); syncs APScheduler jobs |
| `POST` | `/api/v1/integrations/telegram/digest` | Manual morning report (legacy path) |
| `POST` | `/api/v1/integrations/telegram/reports/{job_type}/run` | Manual fire: `morning` \| `midday` \| `night` \| `weekly` \| `ai_briefing` |
| `GET` | `/api/v1/integrations/telegram/report-runs` | Recent audit rows (`?job_type=&limit=`) |

All of the above require auth. Delivery always goes through `build_user_notifier` — domain code never imports `TelegramClient` for reports.

---

## Architecture (short)

```text
API lifespan
  → start_scheduler()          # outbox 30s + reminder poll 10m
  → load_all_scheduled_jobs()  # per-user morning/midday/night/weekly/ai crons

Cron / poll tick
  → ScheduledReportService.run / ReminderScanner.scan_user
  → gate: telegram enabled + pref on
  → scheduled_report_runs (started → sent|skipped|failed)
  → report_builders / reminder templates
  → chunk_text → Notifier → Telegram
```

On prefs save: `IntegrationService.save_telegram_config` → `sync_user_jobs(...)`.

---

## How to test quickly

### Automated

```bash
cd backend && source .venv/bin/activate
pytest app/tests/test_scheduled_reports.py -q
```

### Manual fire (no waiting for cron)

1. Enable Telegram in Settings with a real bot token + chat id.
2. Use **Send morning now** (and siblings) in Scheduled reports, or:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/integrations/telegram/reports/morning/run

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/integrations/telegram/report-runs
```

3. Disable Telegram → run again → expect `skipped` / `telegram_disabled`.

### Reminder dry-runs

| Kind | Setup |
|------|--------|
| Birthday | Event kind Birthday; date = today / +1 / +2 days |
| Immutable | Kind Immutable; start ≈ now + 59 minutes |
| Routine | Block start ≈ now + 2–5 minutes (today’s weekday, not skipped) |

Confirm one audit row per offset; next poll must not duplicate.

More detail: [aidlc-docs/construction/scheduled-reports/build-and-test.md](../aidlc-docs/construction/scheduled-reports/build-and-test.md).

---

## Non-goals / known limits

- No chart / image attachments (`sendPhoto`) in this phase.
- Single-process APScheduler (no Celery / multi-worker HA).
- Quiet hours for reminders: deferred.
- Habit “completed today” uses UTC while reports use user TZ (near-midnight IST edge cases).
- Existing connections that explicitly stored `timezone: "UTC"` keep UTC; IST applies when unset.

---

## Key source files

| Area | Path |
|------|------|
| Scheduler | `backend/app/modules/integrations/scheduler.py` |
| Report service | `backend/app/modules/integrations/scheduled_report_service.py` |
| Builders | `backend/app/modules/integrations/report_builders.py` |
| Reminder poller | `backend/app/modules/integrations/reminder_scanner.py` |
| Audit model | `backend/app/modules/integrations/report_models.py` |
| Prefs | `backend/app/modules/integrations/telegram_config.py` |
| Calendar yearly / kind | `backend/app/modules/calendar/` |
| Routine ↔ habits | `backend/app/modules/routines/models.py` (`routine_block_habits`) |
| Angular Settings | `frontend/src/app/features/integrations/` |
| Requirements | `requirements/25July_3.md` |
