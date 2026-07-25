# LifeOS Scheduled Reports, Reminders & Routines — Requirements (25 July 3)

> Product & engineering spec for scheduler-delivered reports, reminder ladders,
> birthday / immutable events, cron audit logging, and habits inside routines.
>
> Builds on Cycle 7 interactive Telegram bot (`25July_2.md`). This cycle is
> **report-first**: cron pushes full data; interactive screens are optional.

---

# 1. Mission

Deliver reliable, self-contained **scheduled reports and reminders** to Telegram
for users with an **enabled Telegram** `integration_connections` row.

- Prefer extending `DigestService`, `scheduler.py`, calendar recurrence, and
  routines — do not invent a second scheduling product.
- Business logic stays in domain modules; Telegram only formats and sends.
- Default timezone for product defaults and docs: **IST (`Asia/Kolkata`)**.

---

# 2. Locked decisions

| Topic | Decision |
|-------|----------|
| Timezone default | `Asia/Kolkata` (IST) |
| Morning report | **06:00 IST** daily |
| Midday nudge | **12:30 IST** daily |
| Night wrap | **22:00 IST** daily (not “evening”) |
| Weekly review | **Sunday 18:00 IST** |
| Event reminder poller | Every **10 minutes** |
| AI briefing (optional) | **08:00 IST** daily — separate job |
| Images / `sendPhoto` | **Out of scope** this phase |
| Interactive screens as primary report UX | **No** — text reports are self-contained |
| Who gets crons | Only `provider=telegram` AND `enabled=true` |
| Birthday / immutable events | Flag + yearly recurrence; reminder ladders below |

---

# 3. Non-goals (this phase)

- Chart / image attachments in Telegram.
- Second scheduler (Celery, system crontab) unless API process reliability is
  explicitly revisited later.
- Breaking existing digest delivery or interactive bot screens.
- Duplicating business logic inside `integrations/telegram/screens`.

---

# 4. Eligibility

Every scheduled job **must**:

1. Resolve `IntegrationConnection` where `provider == "telegram"` and
   `enabled == true` for that `user_id`.
2. If missing or disabled → **do not send**; log run as `skipped` /
   `telegram_disabled`.
3. Respect per-job prefs toggles (morning / midday / night / weekly / reminders).
4. On startup, register jobs only via `list_enabled_telegram()` (same pattern as
   today). On Telegram disable or prefs off → remove jobs.

---

# 5. Cron suite (IST)

| Job type | APScheduler id pattern | Default (IST) | Frequency | Skip if empty? |
|----------|------------------------|---------------|-----------|----------------|
| `morning` | `telegram_morning_{user_id}` | **06:00** | Daily | No (send “all clear”) |
| `ai_briefing` | `telegram_ai_{user_id}` | **08:00** | Daily (optional toggle) | If off / no API key |
| `midday` | `telegram_midday_{user_id}` | **12:30** | Daily | Yes |
| `night` | `telegram_night_{user_id}` | **22:00** | Daily | No |
| `weekly` | `telegram_weekly_{user_id}` | **Sun 18:00** | Weekly | No |
| `reminder_poll` | `telegram_reminders_{user_id}` or shared poller | every **10 min** | Interval | Yes (most ticks no-op) |

### Day shape (IST)

```text
06:00  Morning report
08:00  AI briefing (optional)
12:30  Midday nudge
22:00  Night wrap
Sun 18:00  Weekly review
*/10   Reminder poller (birthdays, immutable events, routine lead-times)
```

Prefs store local clock times; triggers use `Asia/Kolkata` (or user override,
defaulting to IST).

---

# 6. Report contents (text only)

## 6.1 Morning report (06:00 IST)

Self-contained HTML message:

1. **Routine today** — `RoutineService.today_preview` (honor `skip_dates`).
2. **Pending tasks** — grouped: Overdue / Due today / Later (cap + “+N more”).
3. **Calendar** — today → **+7 days minimum**, titles + times; include expanded
   yearly birthdays / immutable events.
4. **Habits open** — not completed today + streak when available.
5. **Goals** — short top active list with progress %.

No interactive screens required. Optional one-line footer is OK.

## 6.2 Midday nudge (12:30 IST)

Overdue + due-today tasks only. Skip send if none.

## 6.3 Night wrap (22:00 IST)

- Tasks completed today (count + short list).
- Habits still open.
- **Tomorrow:** routine preview + calendar + tasks due tomorrow.

## 6.4 Weekly review (Sunday 18:00 IST)

- Goal progress summary.
- Habit streak highlights.
- Next 7 days calendar (including birthdays).

## 6.5 AI briefing (optional, 08:00 IST)

Separate job calling existing AI/report helpers. Must not block morning report.

## 6.6 Delivery rules

- Via Notifier registry (no domain → `TelegramClient` imports).
- Respect Telegram ~4096 char limit: truncate or split Part 1 / Part 2.
- Manual “send morning now” reuses / extends
  `POST /api/v1/integrations/telegram/digest`.

---

# 7. Calendar: yearly birthdays & immutable events

## 7.1 Yearly recurrence

Today recurrence is `none | daily | weekly | monthly` only.

**Required:** add **`yearly`** to calendar recurrence and expand in
`CalendarService._expand_recurring_event` (same month/day each year).

- Feb 29: in non-leap years use **Feb 28** (document this rule).
- One master event row; **do not** clone a new row each year.

## 7.2 Immutable / non-changeable flag

Add an additive flag on calendar events, e.g.:

- `immutable: bool` (default `false`), **or**
- `event_kind: normal | birthday | immutable`

**Semantics**

- User creates once (e.g. “Birthday — Alice”).
- Marked immutable / birthday → treated as **non-changeable** for reminder
  policy (ladder below). Editing title/date still possible in UI unless product
  later locks fields; **reminder schedule must not require reconfiguration
  per person each year**.
- Birthday implies `recurrence=yearly` (+ birthday reminder ladder).

## 7.3 Birthdays in reports

Morning / night / weekly calendar sections must include expanded birthday
occurrences for the window.

---

# 8. Reminder ladders (poller every 10 min)

A single interval job scans upcoming occurrences and sends Telegram reminders
when the lead-time window is hit (idempotent: one send per
`user + event_occurrence + reminder_offset` — use `scheduled_report_runs` or a
small `reminder_dispatches` uniqueness key).

## 8.1 Birthday events

Offsets relative to birthday **local date (IST)**:

| When | Offset |
|------|--------|
| 2 days before | T−2 days (e.g. morning window or same clock as poller match) |
| 1 day before | T−1 day |
| On birthday morning | **11:55 IST** on the birthday date |

Message example: `🎂 Birthday tomorrow: Alice` / `🎂 Today: Alice`.

## 8.2 Other immutable (non-changeable) events

Offsets before event start:

| Offset |
|--------|
| 7 days |
| 3 days |
| 1 day |
| 6 hours |
| 1 hour |
| **59 minutes** (1 hour − 1 minute) |

## 8.3 Routine blocks

For each of today’s (and near-term) routine blocks, remind before `start_time`:

| Offset |
|--------|
| 30 minutes |
| 15 minutes |
| 5 minutes |
| 1 minute |

Honor `skip_dates` (no reminders that day).

## 8.4 Reminder rules

- Only for users with Telegram enabled.
- Quiet hours optional later (default: none for this phase, except do not
  spam duplicate offsets).
- Reminder body is text-only; no images.
- Dedupe aggressively so a 10-min poller does not re-send the same offset.

---

# 9. Habits inside routines

## 9.1 Goal

User can **attach one or more habits to a routine block** so the daily schedule
and habit tracking stay linked.

## 9.2 Model (additive)

On `routine_blocks` (or a join table):

- `habit_id` nullable FK → `habits.id`, **or**
- `routine_block_habits(block_id, habit_id)` for many habits per block.

Preferred for flexibility: **join table** (many habits per block).

## 9.3 Behaviour

- Creating/editing a routine block allows selecting existing habits.
- Morning report / night wrap may show habits linked to today’s blocks.
- Completing a habit remains via `HabitService` (no duplicate completion logic).
- Optional later: routine reminder message includes linked habit names;
  one-tap complete stays on interactive bot (not required for cron text).

## 9.4 Non-goals

- Do not auto-complete habits when a block’s time passes unless explicitly
  added in a later phase.

---

# 10. Cron run audit table

## 10.1 Table `scheduled_report_runs`

Persist every triggered cron / reminder attempt per user.

| Column | Type | Notes |
|--------|------|--------|
| `id` | VARCHAR(36) PK | UUID |
| `user_id` | VARCHAR(36) indexed | FK users |
| `connection_id` | VARCHAR(36) nullable | Telegram connection |
| `job_type` | VARCHAR(32) indexed | `morning`, `midday`, `night`, `weekly`, `ai_briefing`, `birthday_reminder`, `immutable_reminder`, `routine_reminder`, … |
| `job_id` | VARCHAR(80) | APScheduler id |
| `status` | VARCHAR(16) indexed | `started`, `sent`, `skipped`, `failed` |
| `skip_reason` | VARCHAR(64) nullable | `telegram_disabled`, `prefs_off`, `empty`, `duplicate` |
| `error` | TEXT nullable | No secrets |
| `sections_json` | TEXT nullable | Counts / meta |
| `dedupe_key` | VARCHAR(191) nullable unique | Idempotency for reminders |
| `message_chars` | INTEGER nullable | |
| `scheduled_for` | TIMESTAMPTZ nullable | |
| `started_at` | TIMESTAMPTZ | |
| `finished_at` | TIMESTAMPTZ nullable | |
| `created_at` | TIMESTAMPTZ | |

Indexes: `(user_id, job_type, created_at DESC)`, `(status, created_at)`,
unique on `dedupe_key` where not null.

## 10.2 Flow

1. Job fires → verify Telegram enabled → else `skipped`.
2. Insert `started` (or upsert by `dedupe_key` for reminders).
3. Build + send → `sent` / `failed` / `skipped`.

Retention: 30–90 days optional cleanup later.

---

# 11. Preferences (additive)

Extend Telegram prefs JSON (plaintext alongside encrypted secrets), defaults IST:

| Pref | Default |
|------|---------|
| `timezone` | `Asia/Kolkata` |
| `morning_enabled` / time | true / `06:00` (may map from current `digest_*`) |
| `midday_enabled` / time | true / `12:30` |
| `night_enabled` / time | true / `22:00` |
| `weekly_enabled` | true / Sun `18:00` |
| `ai_briefing_enabled` | false / `08:00` |
| `birthday_reminders_enabled` | true |
| `immutable_reminders_enabled` | true |
| `routine_reminders_enabled` | true |

Sync APScheduler jobs on prefs save (extend `sync_user_digest_job` pattern).

---

# 12. Implementation order

1. `scheduled_report_runs` model + write helpers; gate all jobs on Telegram enabled.
2. Enrich morning report (routine, pending groups, calendar 7d, habits, goals) at **06:00 IST**.
3. Night wrap at **22:00 IST**; midday at **12:30 IST**.
4. Calendar `yearly` recurrence + immutable/birthday flag.
5. Reminder poller: birthdays (T−2, T−1, 11:55 IST day-of), immutable ladder, routine lead-times.
6. Habits ↔ routine blocks linking (API + UI + report mention).
7. Weekly review + optional AI job.
8. Docs: update `docs/TELEGRAM_BOT_GUIDE.md`.

Images remain deferred.

---

# 13. Definition of done

- [ ] Morning / midday / night / weekly fire only for enabled Telegram users (IST defaults above).
- [ ] Morning includes routine, grouped pending, ≥7-day calendar, habits, goals.
- [ ] Night wrap at 22:00 IST with tomorrow preview.
- [ ] Yearly birthdays expand every year without cloning rows.
- [ ] Birthday reminders: 2d, 1d, 11:55 IST on day.
- [ ] Immutable event reminders: 7d, 3d, 1d, 6h, 1h, 59m.
- [ ] Routine reminders: 30m, 15m, 5m, 1m before blocks.
- [ ] Habits can be attached to routine blocks.
- [ ] Every run logged in `scheduled_report_runs` with skip/fail reasons.
- [ ] No image sending required.
- [ ] Tests for report builders, yearly expand, reminder dedupe, Telegram gate.
- [ ] User-facing docs updated.

---

# 14. Stop conditions

Stop and propose if:

- Reminder volume requires a separate worker (process downtime risk).
- Schema changes beyond additive columns / join tables / prefs JSON.
- Idempotency cannot be guaranteed without a unique constraint design.

---

# 15. Remaining / follow-ups (explicit backlog)

Called out so nothing is silently dropped:

| Item | Status |
|------|--------|
| Image / chart attachments in Telegram | Deferred |
| External cron / multi-worker HA for APScheduler | Deferred (single process today) |
| Quiet hours for reminders | Optional later |
| Lock immutable event fields in UI (read-only after create) | Optional; flag + yearly is enough for v1 |
| Auto-complete habit when routine block ends | Out of scope |
| Feb 29 birthday policy | Specified (→ Feb 28); confirm in QA |
| Frontend Settings UI for all new toggles/times | Required for usability — include in construction |
| Migrate existing `digest_*` prefs → `morning_*` | Prefer alias/map, don’t break current Settings |
| Per-reminder Telegram rate limits | Monitor; batch if needed |

---

# 16. Cursor / AI-DLC notes

- One AI-DLC cycle for this requirements file unless split by user.
- Reuse services: `TaskService`, `CalendarService`, `RoutineService`,
  `HabitService`, `GoalService`, `DigestService`, `Notifier`, APScheduler.
- Never implement images “while you’re there.”
- Birthday = yearly + birthday reminder ladder; other immutable events use the
  longer ladder; routines use the short lead-time ladder.
