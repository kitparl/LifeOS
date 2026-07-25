# LifeOS Telegram Bot — User Guide

How to use the LifeOS bot in Telegram. You mostly tap buttons; typing is only needed for titles, search, and a few free-text flows.

If you have not connected Telegram yet, open **Settings → Integrations → Telegram** in the LifeOS web app, save your bot token and chat id, then send `/start` to the bot.

---

## Quick start

1. Open your LifeOS bot in Telegram.
2. Send **`/start`** or **`/dashboard`**.
3. Tap a section (Tasks, Habits, Goals, …).
4. Use the footer buttons on every screen:

| Button | What it does |
|--------|----------------|
| ⬅ Back | Go to the previous screen |
| 🔄 Refresh | Reload the current screen |
| 🏠 Home | Return to the dashboard |

To cancel a multi-step flow (e.g. “add task” waiting for a title), send **`/cancel`**.

---

## All slash commands

You can type these anytime. Many of them open the same interactive screens as the dashboard buttons.

| Command | What it does |
|---------|----------------|
| `/start` | Opens the interactive home dashboard |
| `/dashboard` | Same as `/start` — home with all section buttons |
| `/help` | Lists commands |
| `/tasks` | Open tasks (tap Done / View / Due — no typing IDs) |
| `/today` | Today’s calendar |
| `/add-task <title>` | Create a task in one message (optional due date) |
| `/done <id>` | Complete a task by the 8-character code from `/tasks` |
| `/habits` | Habits due today — one-tap complete |
| `/goals` | Active goals |
| `/search <query>` | Search tasks, goals, habits, calendar, and more |
| `/search` | Starts a search conversation (bot asks for a keyword) |
| `/cancel` | Cancel the current conversation (add task, note, search, AI, …) |

### `/add-task` examples

```text
/add-task Buy milk
/add-task Call dentist due 2026-08-01
/add-task Pay rent tomorrow
/add-task Review slides today
```

Default due date is **today** if you do not specify one.

### `/done` tip

Prefer tapping **✅ Done** on the Tasks screen. If you use the command, copy the short code in brackets from `/tasks`, for example:

```text
/done abcdef12
```

---

## Home dashboard

Send `/dashboard` (or `/start`). You get these buttons:

| Button | Opens |
|--------|--------|
| 📋 Tasks | Open task list |
| 📅 Today | Today’s calendar |
| 🔁 Habits | Habits for today |
| 🎯 Goals | Active goals |
| 🗓 Calendar | This week’s events |
| ⏱ Routines | Routines and today’s blocks |
| 📝 Notes | Quick capture / search notes |
| ⚙️ Automations | Rules list, pause/resume, run all |
| 📊 Analytics | 30-day summary card |
| 🔍 Search | Universal search |
| 🤖 AI Briefing | Daily AI review + helpers |

---

## Features by area

### Tasks

**Open:** `/tasks` or dashboard → Tasks

- Numbered list with status emoji and due date
- Per task: **✅ Done**, **👁 View**, **📅 Due date**
- Pagination if you have many tasks
- **➕ Add task** — bot asks for a title, then a due date (Today / Tomorrow / +3 days / +1 week, or type `YYYY-MM-DD`)

You never need to type a task UUID for the button flows.

### Calendar

**Open:** `/today`, or dashboard → Today / Calendar

- **Today** — events for today, tap to open detail
- **Week** — next 7 days
- Event detail shows time, location, and description when available

### Habits

**Open:** `/habits` or dashboard → Habits

- Each habit shows streak (🔥)
- Tap **✅** to mark complete for today
- Tap **↩️ Undo** if you marked by mistake

### Goals

**Open:** `/goals` or dashboard → Goals

- List of active goals with progress %
- Open a goal to see:
  - Milestones (tap ✅ to complete one)
  - Linked tasks (tasks that belong to that goal)

### Routines

**Open:** dashboard → Routines

- List of active routines and today’s time blocks
- Open a routine to see its steps
- **⏭ Skip today** / **↩️ Unskip today** (uses the routine’s skip dates — does not mark “done”, because routines are schedules)

### Notes (quick capture)

**Open:** dashboard → Notes

| Action | How |
|--------|-----|
| Capture | Tap **➕ Capture note**, then send plain text. First line = title; rest = body. Saved under **Telegram Inbox → Quick Capture** in Knowledge Notes |
| Search notes | Tap **🔍 Search notes**, then send a keyword |
| Subjects | See your knowledge subjects overview |

### Automations

**Open:** dashboard → Automations

- See each rule: on/off, trigger, last run time
- **⏸ Pause** / **▶️ Resume** a rule
- **▶️ Run all now** — evaluates all rules once and shows what triggered

### AI assist

**Open:** dashboard → AI Briefing

- **Daily briefing** — short focus review from your LifeOS data
- **🧩 Break down a task** — send a task; get numbered steps
- **➕ NL add task** — describe a task in plain language; LifeOS creates it (uses AI when configured, otherwise a simple parse)

### Analytics

**Open:** dashboard → Analytics

- Life score, tasks today, completion, goal/habit scores, journal streak, overdue count, focus hours
- For full charts, use the web **Analytics** dashboard

### Search

**Open:** `/search milk` or dashboard → Search

- Searches across tasks, goals, habits, calendar, journal, and related modules
- Results are paginated — use ◀ ▶ to move pages

### Attachments (photos / files / voice)

- Send a **photo**, **document**, or **voice note** to the bot
- LifeOS stores it via the Files module
- If you started an “attach to task” flow, it links to that task; otherwise it is stored as a Telegram attachment

---

## Notifications & scheduled reports

These arrive from LifeOS without you typing anything.

### Instant notifications (when enabled in Settings)

When something is created (e.g. a new task) and you opted in, Telegram gets a message.

**New task** messages include buttons:

- ✅ Mark done  
- 👁 View  
- 📋 Tasks  
- 🏠 Home  

### Scheduled reports (IST defaults)

Configure under **Settings → Integrations → Telegram → Scheduled reports**. Only users with Telegram **enabled** receive them.

For the full engineering guide (cron suite, reminder ladders, audit table, APIs), see **[SCHEDULED_REPORTS.md](./SCHEDULED_REPORTS.md)**.

| Report | Default (Asia/Kolkata) | Contents |
|--------|------------------------|----------|
| Morning | 06:00 daily | Routine today, pending tasks (Overdue / Due today / Later), calendar next 7 days, habits open, goals |
| AI briefing | 08:00 daily (off by default) | Optional AI daily review |
| Midday nudge | 12:30 daily | Overdue + due-today only (skipped if empty) |
| Night wrap | 22:00 daily | Completed today, habits still open, tomorrow preview |
| Weekly review | Sunday 18:00 | Goal progress, habit streaks, next 7 days |

Use **Send morning now** (and siblings) in Settings to fire a report immediately. Every attempt is logged in `scheduled_report_runs` (visible as recent runs in Settings).

### Reminder ladders (every 10 minutes)

| Kind | Offsets |
|------|---------|
| Birthdays (`event_kind=birthday`, yearly) | 2 days before, 1 day before, **11:55** on the day |
| Immutable events | 7d, 3d, 1d, 6h, 1h, 59m before start |
| Routine blocks | 30m, 15m, 5m, 1m before start (honours skip dates) |

Each reminder is sent at most once (deduped). Toggle birthday / immutable / routine reminders in Settings.

### Calendar birthdays & habits on routines

- Create a calendar event with **Event kind → Birthday** (forces yearly recurrence). Feb 29 birthdays use Feb 28 in non-leap years.
- Attach habits to routine blocks in the Routines editor; morning/night reports can mention linked habits.

---

## Conversations (when the bot asks you to type)

Some flows wait for your next message:

| Flow | What to send | Cancel |
|------|----------------|--------|
| Add task | Title, then due date if asked | `/cancel` |
| Set due date by typing | `today`, `tomorrow`, or `YYYY-MM-DD` | `/cancel` |
| Note capture | Note text | `/cancel` |
| Note / universal search | Keyword | `/cancel` |
| AI breakdown / NL task | Free text | `/cancel` |

While a conversation is active, plain text goes to that flow (not treated as a random chat message). Slash commands still work; `/cancel` exits the flow.

---

## Tips

- Prefer **buttons** over typing IDs.
- Short codes like `abcdef12` appear in task lines for `/done` only — they are safe prefixes, not full database IDs in the visible UI for button actions.
- If a screen looks stale, tap **🔄 Refresh**.
- If the bot stops responding mid-flow after a server restart, send `/dashboard` again (conversation state is in memory and resets on restart).
- Classic text commands (`/done`, `/add-task`) still work for power users and scripts.

---

## Setup checklist (one time)

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Message your bot once, then detect chat id in LifeOS Settings → Integrations → Telegram (or use the detect-chat-id action).
3. Save token + chat id and enable the connection.
4. **Local / no public URL:** set `TELEGRAM_POLLING_ENABLED=true` in `backend/.env` and restart the API.
5. **Production:** set `PUBLIC_BASE_URL` and use **Register webhook** in Settings.
6. Optionally enable event notifications and scheduled reports (morning / midday / night / weekly) plus reminder toggles.

For engineer-oriented details (outbox, encryption, env vars), see [TELEGRAM_NOTIFIER.md](./TELEGRAM_NOTIFIER.md).
