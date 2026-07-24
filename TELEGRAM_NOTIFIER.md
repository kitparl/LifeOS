# Telegram Notifier — What Was Built & How to Use It

This guide covers the one-way Telegram integration added to LifeOS: what shipped, how to configure it, and how to verify it works.

---

## What was built

### Backend
- **Encrypted storage** of each user’s bot token and chat id in `IntegrationConnection.config_json` (Fernet encryption at rest).
- **`TelegramClient`** — thin async adapter calling Telegram Bot API (`sendMessage`, `getMe`, `getUpdates`).
- **`Notifier` abstraction** — callers send messages without knowing about Telegram; a registry builds the right channel per user.
- **Endpoints** (all require login):
  - `GET /api/v1/integrations/telegram` — status (masked token, never raw secret)
  - `PUT /api/v1/integrations/telegram/config` — save bot token / chat id / enabled
  - `POST /api/v1/integrations/{conn_id}/test` — send a test message
  - `POST /api/v1/integrations/{conn_id}/detect-chat-id` — discover chat ids via `getUpdates`
  - `POST /api/v1/integrations/telegram/digest` — send a digest of tasks, calendar, races, habits, goals
- **Notifications module** — `send_telegram()` now actually sends via the user’s Telegram config (stub removed).
- **DB** — `last_digest_at` column on `integration_connections` (added via `ensure_columns` on startup).

### Frontend
- Integrations page: Telegram card with setup guide, bot token (password field), chat id, Detect / Save / Test / Send digest buttons, and connection status.

### Not in this release
- Two-way chat / webhooks / polling for commands
- Automatic scheduled digests (the digest service is ready; call it from a cron/scheduler later)

---

## What you need to do

### 1. Backend env (recommended)

In `backend/.env` (copy from `.env.example` if needed):

```bash
# Existing
SECRET_KEY=your-secret-key
ENV=dev

# Recommended for production (and fine for local too):
# Generate with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
INTEGRATION_ENC_KEY=<paste-generated-key-here>
```

Notes:
- If `INTEGRATION_ENC_KEY` is unset, LifeOS derives a key from `SECRET_KEY`. That works, but changing `SECRET_KEY` later will make old encrypted tokens unreadable — prefer a dedicated `INTEGRATION_ENC_KEY`.
- **Never commit** real keys or bot tokens to git.
- **Production**: serve the API only over HTTPS (TLS at your reverse proxy / VPS).

### 2. Run the apps

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate   # or use .venv/bin/python
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm start
```

Open the app (usually `http://localhost:4200`), log in, go to **Integrations**.

### 3. Create your Telegram bot

1. In Telegram, open **@BotFather**.
2. Send `/newbot` and follow the prompts.
3. Copy the **HTTP API token** BotFather gives you.
4. Open a chat with your new bot and press **Start** (or send any message).  
   If you want group notifications, add the bot to the group and send a message there.

### 4. Configure LifeOS

On the **Integrations** page → **Telegram** card:

1. Expand **How to integrate your bot** if you want the on-screen checklist.
2. Paste the bot token into **Bot Token**.
3. Click **Detect chat id** (or paste a chat id manually).  
   Fallback: message **@userinfobot** in Telegram and copy your Id.
4. Ensure **Enable Telegram notifications** is checked.
5. Click **Save**.
6. Click **Send test message** — you should get a confirmation in Telegram.
7. Optionally click **Send digest** to push a summary of pending tasks, calendar, races, habits, and goals.

### 5. Optional checks

```bash
# Backend unit tests for this feature
cd backend
.venv/bin/python -m pytest app/tests/test_telegram_notifier.py -v
```

---

## API quick reference (authenticated)

| Action | Method | Path |
|--------|--------|------|
| Status (masked) | GET | `/api/v1/integrations/telegram` |
| Save config | PUT | `/api/v1/integrations/telegram/config` |
| Test send | POST | `/api/v1/integrations/{connection_id}/test` |
| Detect chat id | POST | `/api/v1/integrations/{connection_id}/detect-chat-id` |
| Send digest | POST | `/api/v1/integrations/telegram/digest` |

Example save body:

```json
{
  "bot_token": "123456:ABC...",
  "chat_id": "987654321",
  "enabled": true
}
```

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Detect chat id finds nothing | Message your bot first (press Start), then detect again. Token must be valid. |
| Test fails / Unauthorized | Token wrong or revoked — create a new one with @BotFather and Save again. |
| Test fails / chat not found | Wrong chat id, or bot was never started in that chat/group. |
| Digest says not configured | Save token + chat id and leave **Enable** on. |
| Saved tokens stop decrypting | `SECRET_KEY` / `INTEGRATION_ENC_KEY` changed — set a stable `INTEGRATION_ENC_KEY` and re-enter the bot token. |
| Frontend `@BotFather` build error | Already fixed: templates use `&#64;` for literal `@`. Restart `npm start` if needed. |

---

## Later extensions (design already supports)

- **Scheduled digests**: call `DigestService(db).send_digest(user_id)` from a cron/worker (same method the manual endpoint uses).
- **Two-way bots**: add webhook/polling + optional `receive` on the Notifier; keep existing `send` callers unchanged.
- **Extra bots/channels**: register another builder in `NOTIFIER_BUILDERS` with its own provider key and encrypted `config_json`.

---

## Key files

| Area | Path |
|------|------|
| Crypto | `backend/app/core/crypto.py` |
| Telegram client | `backend/app/modules/integrations/telegram_client.py` |
| Notifier + registry | `backend/app/modules/integrations/notifier.py`, `notifier_registry.py` |
| Digest | `backend/app/modules/integrations/digest_service.py` |
| API / service | `backend/app/modules/integrations/api.py`, `service.py` |
| Frontend | `frontend/src/app/features/integrations/` |
| Env example | `backend/.env.example` |
