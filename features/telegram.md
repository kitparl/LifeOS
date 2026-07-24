# Feature: Telegram Integration

LifeOS can send you notifications in Telegram and let you query/complete work from the chat. This document is the full feature reference (setup, outbound pushes, digests, bot commands, and architecture).

---

## Overview

| Capability | Description |
|------------|-------------|
| **Outbound push** | Instant Telegram message when you create certain entities in LifeOS |
| **Digest** | Scheduled or on-demand summary of tasks, calendar, races, habits, goals |
| **Two-way bot** | Reply to commands like `/tasks` from your Telegram chat |
| **Config UI** | Integrations page: token, chat id, event toggles, digest schedule, webhook |

Credentials (bot token + chat id) are stored encrypted at rest. Source modules (tasks, running, etc.) never import Telegram code — they only emit domain events.

---

## Setup

### 1. Environment (`backend/.env`)

```bash
INTEGRATION_ENC_KEY=<Fernet key>   # recommended; else derived from SECRET_KEY
PUBLIC_BASE_URL=https://your-host # required for webhook (no trailing slash)
TELEGRAM_POLLING_ENABLED=false    # true = local/dev long-poll without HTTPS
```

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Create a bot

1. In Telegram, open **@BotFather** → `/newbot` → copy the HTTP API token.
2. Open a chat with your bot and press **Start**.

### 3. Connect in LifeOS

1. Open **Integrations** → **Telegram**.
2. Paste **Bot Token**, **Detect chat id** (or paste chat id), enable notifications → **Save**.
3. **Send test message** to verify.
4. Optionally set **Notify on events**, **Scheduled digest**, and **Register webhook**.

---

## Outbound: when LifeOS messages you

### A. Real-time event pushes (on create)

Only **create** actions emit events (not update/delete). The matching toggle under **Notify on events** must be on, and Telegram must be enabled + configured.

| App action | Event key | Example message |
|------------|-----------|-----------------|
| Create task | `task_created` | `New task added: Buy milk (due 2026-07-25)` |
| Create race | `race_added` | `New race added: City 10K on 2026-08-01` |
| Create calendar event | `calendar_event_created` | `New calendar event: Standup at 2026-07-24 09:00` |
| Create habit | `habit_created` | `New habit created: Meditate (daily)` |
| Create goal | `goal_created` | `New goal created: Ship Phase 2 (target 2026-08-01)` |
| Add goal milestone | `goal_milestone_added` | `Goal milestone added: Ship Phase 2: Docs done` |

**Delivery path:** create → domain event → outbox row (`pending_notifications`) in the same DB transaction → after commit, dispatcher sends via Notifier → Telegram. Failures retry; they never roll back the create once the table exists.

### B. Digest

Aggregates pending tasks, upcoming calendar, upcoming races, habits due, active goals.

| Trigger | When |
|---------|------|
| **Send digest now** | Immediately (Integrations UI or `POST /api/v1/integrations/telegram/digest`) |
| **Scheduled digest** | At configured time / frequency / timezone (APScheduler per-user cron) |

Digest prefs in config: `digest_enabled`, `digest_time` (`HH:MM`), `digest_frequency` (`daily` \| `weekdays` \| `weekly`), `digest_weekday` (0=Mon…6=Sun), `timezone` (e.g. `Asia/Kolkata`).

### C. Manual test

**Send test message** → `✅ LifeOS Telegram connection test succeeded.`

---

## Two-way: bot commands

Commands work only if **inbound** is active:

- **Production:** Register webhook (`PUBLIC_BASE_URL` + HTTPS), or  
- **Dev:** `TELEGRAM_POLLING_ENABLED=true` (and no webhook on that connection).

The update’s `chat.id` must match the saved chat id; unknown chats are rejected.

Implementation: `backend/app/modules/integrations/command_handler.py` (additive registry — add a dict entry for new commands).

### `/help` (also `/start`)

Lists available commands.

```
LifeOS bot commands:
/tasks — pending tasks
/today — today's agenda
/done <id> — complete a task
/habits — habits due
/goals — active goals
/help — this message
```

### `/tasks`

Lists open tasks (`pending` + `in_progress`), up to 20.

Each line includes a short id prefix you can use with `/done`:

```
Pending tasks:
• [abcdef12] Buy milk (pending, 2026-07-25)
• [12345678] Write docs (in_progress, no due)
```

Empty: `No pending tasks. Nice work!`

### `/today`

Today’s agenda (server date):

- Tasks due today  
- Calendar events overlapping today  
- Races scheduled for today  

```
Today (2026-07-24):

Tasks due today:
• [abcdef12] Buy milk

Calendar:
• 09:00 Standup

Races:
• City 10K
```

Empty: `Nothing scheduled for today.`

### `/done <id>`

Completes one open task. `<id>` is the task UUID or its **prefix** (as shown in `/tasks`, typically first 8 chars).

| Input | Result |
|-------|--------|
| `/done` | `Usage: /done <task_id_prefix>` |
| `/done abcdef12` (unique match) | `Done: Buy milk` |
| Ambiguous prefix | Lists matching tasks |
| No match | `No open task matching '…'.` |

### `/habits`

Active habits not completed for the current period (day/week/month by frequency).

```
Habits due:
• Meditate (daily)
• Weekly review (weekly)
```

Empty: `All active habits completed for this period.`

### `/goals`

Active goals with progress and target date.

```
Active goals:
• Ship Phase 2 · 40% · 2026-08-01
```

Empty: `No active goals.`

### Unknown / non-command text

- Unknown `/command` → hint to try `/help`  
- Plain text (no leading `/`) → `Send a command like /help to get started.`

---

## Enabling inbound (webhook vs polling)

### Webhook (preferred on VPS)

1. Set `PUBLIC_BASE_URL=https://your-api-host`  
2. Integrations → Telegram → **Register webhook**  
3. Telegram POSTs to:  
   `POST /api/v1/integrations/telegram/webhook/{secret}`  
4. Auth: path `webhook_secret` + optional `X-Telegram-Bot-Api-Secret-Token` header  

**Disable webhook** clears the secret and calls Telegram `deleteWebhook`.

### Long polling (dev fallback)

```bash
TELEGRAM_POLLING_ENABLED=true
```

Backend polls `getUpdates` for enabled Telegram connections that do **not** have a webhook secret. Same command handler as webhook.

---

## API reference (authenticated unless noted)

| Action | Method | Path |
|--------|--------|------|
| Status + prefs | GET | `/api/v1/integrations/telegram` |
| Save config / prefs | PUT | `/api/v1/integrations/telegram/config` |
| Test send | POST | `/api/v1/integrations/{connection_id}/test` |
| Detect chat id | POST | `/api/v1/integrations/{connection_id}/detect-chat-id` |
| Send digest now | POST | `/api/v1/integrations/telegram/digest` |
| Register webhook | POST | `/api/v1/integrations/telegram/webhook/register` |
| Webhook status | GET | `/api/v1/integrations/telegram/webhook` |
| Disable webhook | DELETE | `/api/v1/integrations/telegram/webhook` |
| Inbound updates | POST | `/api/v1/integrations/telegram/webhook/{secret}` *(no login; path secret)* |

Example config body:

```json
{
  "bot_token": "123456:ABC...",
  "chat_id": "987654321",
  "enabled": true,
  "notify_on": [
    "task_created",
    "race_added",
    "calendar_event_created",
    "habit_created",
    "goal_created",
    "goal_milestone_added"
  ],
  "digest_enabled": true,
  "digest_time": "08:00",
  "digest_frequency": "daily",
  "digest_weekday": 0,
  "timezone": "Asia/Kolkata"
}
```

---

## Architecture

```
Create entity (tasks/running/calendar/habits/goals)
        │
        ▼
  event_bus.emit(EntityCreated)     ← modules import only app.core.events
        │
        ▼
  integrations subscriber           ← checks enabled + notify_on
        │
        ▼
  pending_notifications (same txn)
        │
        ▼
  DB commit → after_commit nudge / 30s drain
        │
        ▼
  NotificationDispatcher → Notifier → TelegramClient.sendMessage

Inbound:
  Telegram → webhook/{secret} or polling
        │
        ▼
  verify chat_id → CommandHandler → module services → reply via Notifier
```

### Key files

| Area | Path |
|------|------|
| Event bus | `backend/app/core/events.py` |
| Crypto | `backend/app/core/crypto.py` |
| Outbox | `backend/app/modules/integrations/outbox_models.py`, `outbox_repository.py`, `dispatcher.py` |
| Subscriber | `backend/app/modules/integrations/subscriber.py` |
| Commands | `backend/app/modules/integrations/command_handler.py` |
| Webhook / polling | `webhook_service.py`, `polling.py` |
| Scheduler | `backend/app/modules/integrations/scheduler.py` |
| Client / config | `telegram_client.py`, `telegram_config.py` |
| Digest | `digest_service.py` |
| UI | `frontend/src/app/features/integrations/` |
| Ops guide | `TELEGRAM_NOTIFIER.md` |

---

## Security notes

- Bot tokens are Fernet-encrypted; API responses only show a masked token.  
- Never log bot tokens.  
- Webhook is authenticated by per-connection secret; unknown chat ids are rejected.  
- Serve the API over HTTPS in production when handling tokens / webhooks.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Detect chat id empty | Message the bot first, then detect again |
| Test Unauthorized | Bad/revoked token — new token from BotFather |
| Webhook register fails | Set `PUBLIC_BASE_URL` to public HTTPS API base |
| Commands ignored | Register webhook or enable polling; chat id must match |
| Push missing | Event toggled in `notify_on`, Telegram enabled, server running |
| Digest wrong time | Check timezone + digest enabled + Save |
| Tokens won’t decrypt | Stable `INTEGRATION_ENC_KEY`; re-enter bot token |

---

## Tests

```bash
cd backend
.venv/bin/python -m pytest app/tests/test_telegram_notifier.py app/tests/test_telegram_phase2.py -v
```
