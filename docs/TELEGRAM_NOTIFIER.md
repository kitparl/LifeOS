# Telegram Notifier — What Was Built & How to Use It

> **Looking for how to use the bot day-to-day?**  
> Read the plain-language guide: **[TELEGRAM_BOT_GUIDE.md](./TELEGRAM_BOT_GUIDE.md)** (all commands, buttons, and features).

This document covers the Telegram integration in LifeOS from an engineering / setup angle (Phase 1 one-way + Phase 2 event push / two-way commands / digests + **Cycle 7 interactive UI**).

---

## What was built

### Phase 1 — One-way outbound
- **Encrypted storage** of each user’s bot token and chat id in `IntegrationConnection.config_json` (Fernet encryption at rest).
- **`TelegramClient`** — thin async adapter (`sendMessage`, `getMe`, `getUpdates`, `setWebhook`, `deleteWebhook`, `getWebhookInfo`, plus Cycle 7: `editMessageText`, `answerCallbackQuery`, `getFile`).
- **`Notifier` abstraction** — callers send messages without knowing about Telegram; a registry builds the right channel per user. Supports optional `reply_markup` (inline keyboards).
- Endpoints for status / config / test / detect-chat-id / manual digest.

### Phase 2 — Events, two-way, scheduling
- **Domain event bus** (`app.core.events`) — tasks/running/calendar/habits/goals emit `EntityCreated` on create (no Telegram imports).
- **Transactional outbox** (`pending_notifications`) — integrations subscriber writes a row in the same DB transaction; a dispatcher delivers after commit via Notifier (retries on failure). Outbox rows may carry `reply_markup_json` for actionable notifications.
- **Per-event toggles** (`notify_on` in config_json) and **digest schedule** (`digest_enabled`, `digest_time`, `digest_frequency`, `digest_weekday`, `timezone`).
- **Webhook** `POST /api/v1/integrations/telegram/webhook/{secret}` + register/status/delete helpers; unknown chat ids rejected.
- **Commands**: `/help`, `/tasks`, `/today`, `/done <id>`, `/habits`, `/goals` (additive registry).
- **Long-polling fallback** when `TELEGRAM_POLLING_ENABLED=true` (dev; skip connections that have a webhook).
- **APScheduler** (`AsyncIOScheduler`) in app lifespan: per-user digest cron jobs + 30s outbox drain.

### Cycle 7 — Interactive bot (Phases 1–7 of the product roadmap)
- **UI kernel** under `backend/app/modules/integrations/telegram/`: keyboards, callback router, conversation engine, in-memory state, renderer, shared `update_router` used by webhook + polling.
- **Tap-driven screens** for Tasks, Calendar, Habits, Goals (with linked tasks), Routines (skip today), Notes capture, Automations, AI briefing, Analytics, Search, Attachments.
- **`/dashboard`** (also `/start`) — interactive home. Existing slash commands still work and now open interactive screens where available.
- **Actionable notifications** — task-created pushes include Mark done / View buttons; digests include section-jump buttons.
- **AI helpers** on `AiService`: `suggest_task_breakdown`, `parse_and_create_task` (Telegram only displays results).

### Frontend
- Integrations page Telegram card: setup guide, credentials, **notify-on checkboxes**, **digest schedule/timezone**, **webhook register/status**, test / digest buttons.

---

## What you need to do

### 1. Backend env

In `backend/.env` (copy from `.env.example` if needed):

```bash
ENV=dev
SECRET_KEY=your-secret-key

# Recommended:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
INTEGRATION_ENC_KEY=<paste-generated-key-here>

# Required for setWebhook (public HTTPS URL of this API, no trailing slash):
# PUBLIC_BASE_URL=https://lifeos.example.com

# Local/dev without HTTPS: long-poll instead of webhook
# TELEGRAM_POLLING_ENABLED=true
```

Notes:
- Prefer a dedicated `INTEGRATION_ENC_KEY` (changing `SECRET_KEY` alone must not break tokens).
- **Never commit** real keys or bot tokens.
- **Production**: HTTPS only (TLS at reverse proxy / VPS).

### 2. Run the apps

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt   # includes apscheduler
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm start
```

Open the app → **Integrations** → Telegram card.

### 3. Create / connect your bot

1. `@BotFather` → `/newbot` → copy token.
2. Start a chat with the bot.
3. Paste token, **Detect chat id**, enable notifications, **Save**.
4. **Send test message**.
5. Tick which events to notify on; optionally enable scheduled digest + timezone.
6. On a VPS with `PUBLIC_BASE_URL` set: **Register webhook**, then try `/tasks` in Telegram.

### 4. Tests

```bash
cd backend
.venv/bin/python -m pytest app/tests/test_telegram_notifier.py app/tests/test_telegram_phase2.py -v
```

---

## API quick reference

| Action | Method | Path | Auth |
|--------|--------|------|------|
| Status (masked + prefs) | GET | `/api/v1/integrations/telegram` | login |
| Save config / prefs | PUT | `/api/v1/integrations/telegram/config` | login |
| Test send | POST | `/api/v1/integrations/{connection_id}/test` | login |
| Detect chat id | POST | `/api/v1/integrations/{connection_id}/detect-chat-id` | login |
| Send digest now | POST | `/api/v1/integrations/telegram/digest` | login |
| Register webhook | POST | `/api/v1/integrations/telegram/webhook/register` | login |
| Webhook status | GET | `/api/v1/integrations/telegram/webhook` | login |
| Disable webhook | DELETE | `/api/v1/integrations/telegram/webhook` | login |
| Inbound updates | POST | `/api/v1/integrations/telegram/webhook/{secret}` | path secret (+ optional header) |

Example save body:

```json
{
  "bot_token": "123456:ABC...",
  "chat_id": "987654321",
  "enabled": true,
  "notify_on": ["task_created", "race_added", "calendar_event_created", "habit_created", "goal_created", "goal_milestone_added"],
  "digest_enabled": true,
  "digest_time": "08:00",
  "digest_frequency": "daily",
  "digest_weekday": 0,
  "timezone": "Asia/Kolkata"
}
```

---

## Architecture (Phase 2)

```
module.create_*  →  event_bus.emit(EntityCreated)
                         ↓
              integrations subscriber (same txn)
                         ↓
              pending_notifications row
                         ↓
              get_db() commits
                         ↓
         after_commit nudge + APScheduler drain
                         ↓
              NotificationDispatcher → Notifier → Telegram
```

Source modules import only `app.core.events`. Telegram failures never break creates.

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Detect chat id finds nothing | Message your bot first, then detect again. |
| Test fails / Unauthorized | Token wrong — recreate with BotFather. |
| Webhook register fails | Set `PUBLIC_BASE_URL` to HTTPS URL of the API. |
| Commands ignored | Register webhook (or enable polling); chat id must match. |
| Digest not at expected time | Check timezone (e.g. `Asia/Kolkata`) and that digest is enabled + Save. |
| Push not arriving | Ensure event is in `notify_on`, Telegram enabled; check dispatcher/logs. |
| Saved tokens stop decrypting | Set a stable `INTEGRATION_ENC_KEY` and re-enter the bot token. |

---

## Key files

| Area | Path |
|------|------|
| Event bus | `backend/app/core/events.py` |
| Crypto | `backend/app/core/crypto.py` |
| Outbox | `backend/app/modules/integrations/outbox_models.py`, `outbox_repository.py`, `dispatcher.py` |
| Subscriber | `backend/app/modules/integrations/subscriber.py` |
| Commands / webhook / polling | `command_handler.py`, `webhook_service.py`, `polling.py` |
| Scheduler | `backend/app/modules/integrations/scheduler.py` |
| Telegram client / config | `telegram_client.py`, `telegram_config.py` |
| Digest | `digest_service.py` |
| Frontend | `frontend/src/app/features/integrations/` |
| Env example | `backend/.env.example` |
