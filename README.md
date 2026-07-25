# LifeOS — Personal AI Operating System

> **Version:** 1.0 (Personal Alpha)  
> **Author:** Pranshu Bisht  
> **Status:** Phase 3 complete — ready for personal use & private deploy  
> **Architecture:** Offline First • AI Powered • Mobile Friendly • Personal Knowledge System

---

## Quick links

| Document | Purpose |
|----------|---------|
| [PHASE-1.md](docs/PHASE-1.md) | Foundation MVP (auth, goals, tasks, habits, PWA, …) |
| [PHASE-2.md](docs/PHASE-2.md) | Intelligence (AI RAG, learning, finance, analytics, …) |
| [PHASE-3.md](docs/PHASE-3.md) | Full AI OS (memory, coaches, OCR, voice, …) |
| [TELEGRAM_BOT_GUIDE.md](docs/TELEGRAM_BOT_GUIDE.md) | Telegram bot — all commands & features (user guide) |
| [TELEGRAM_NOTIFIER.md](docs/TELEGRAM_NOTIFIER.md) | Telegram — engineer setup, events, digests, env |
| [requirements/v1.md](requirements/v1.md) | Release readiness & what to improve before public v1.0 |
| [DEPLOY_HEROKU.md](docs/DEPLOY_HEROKU.md) | Deploy to Heroku (~$13/mo, GitHub Student) |
| [SSL_CADDY.md](docs/SSL_CADDY.md) | HTTPS / Caddy reverse proxy notes |
| [ROADMAP.md](docs/ROADMAP.md) | Original product roadmap |
| [runProject.md](runProject.md) | Run locally (dev) |

---

## Project status (July 2026)

**All 27 units delivered** (Phase 1: 0–11, Phase 2: 12–18, Phase 3: 19–26).  
**Telegram Phase 2** is live: event push, two-way bot commands, scheduled digests, webhook + polling.

| Area | Status |
|------|--------|
| Feature roadmap | ✅ Complete |
| Personal / private use | ✅ Ready |
| Telegram companion | ✅ Phase 1 + Phase 2 |
| Tests | ✅ 69 backend (pytest) + 14 frontend (Karma) |
| Public production release | ⚠️ See [requirements/v1.md](requirements/v1.md) |

**Not production-complete yet:** Alembic migrations, CI/CD, rate limiting, Playwright e2e, live integration OAuth, full OCR for images/PDF. Fine for personal alpha.

---

## Run locally (development)

**Backend** (port 8000):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt email-validator
cp .env.example .env   # edit SECRET_KEY; set OPENAI_API_KEY / INTEGRATION_ENC_KEY as needed
uvicorn app.main:app --reload --port 8000
```

**Frontend** (port 4200):

```bash
cd frontend
npm install --legacy-peer-deps
npm start
```

Open http://localhost:4200 — API at http://localhost:8000/api/v1.  
Health check: http://localhost:8000/health.  
API docs (dev only): http://localhost:8000/docs.

### Useful env (`backend/.env`)

| Variable | Purpose |
|----------|---------|
| `ENV=dev` | Local development (insecure cookies OK, `/docs` enabled) |
| `SECRET_KEY` | JWT / crypto base |
| `INTEGRATION_ENC_KEY` | Fernet key for bot tokens at rest (recommended) |
| `OPENAI_API_KEY` | Optional — AI chat, coaches, embeddings |
| `PUBLIC_BASE_URL` | HTTPS API URL for Telegram `setWebhook` |
| `TELEGRAM_POLLING_ENABLED=true` | Dev fallback when you have no public HTTPS |

---

## Deploy to Heroku

Single-app deploy: FastAPI serves the Angular build + API. Uses Heroku Postgres.

**Full guide:** [docs/DEPLOY_HEROKU.md](docs/DEPLOY_HEROKU.md)

```bash
heroku create lifeos-yourname
heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY="$(openssl rand -hex 32)" COOKIE_SECURE=true ENV=production
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
git push heroku main
```

For a VPS with HTTPS (needed for Telegram webhooks), see [docs/SSL_CADDY.md](docs/SSL_CADDY.md).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Angular 19 (standalone), Tailwind 4, Dexie, PWA service worker, FullCalendar, TipTap |
| Backend | FastAPI, SQLAlchemy 2 async, Pydantic Settings |
| Database (dev) | SQLite (`aiosqlite`) |
| Database (prod) | PostgreSQL (Heroku Postgres / self-hosted) |
| Auth | JWT access + HttpOnly refresh cookie |
| AI | OpenAI (optional), local RAG index |
| Integrations | Telegram Bot API, Fernet-encrypted secrets, transactional outbox |
| Scheduling | APScheduler (`AsyncIOScheduler`) — digests + outbox drain |
| Tests | pytest / pytest-asyncio, Karma / Jasmine |

---

## Modules (API `/api/v1`)

**Phase 1:** auth, dashboard, goals, tasks, habits, running, calendar, journal, mood, communication, qa, wishlist, knowledge-notes, search, notifications, export, files  

**Phase 2:** ai, learning, career, finance, analytics, timeline, reports  

**Phase 3:** memory, coaches, ocr, voice, integrations, automations, predictions, life-timeline

---

## Creating users (manual)

Registration is disabled in the UI. Create a user via the API:

```bash
# Local development
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword123",
    "display_name": "Your Name"
  }'

# Production (replace YOUR_DOMAIN)
curl -c cookies.txt -X POST https://YOUR_DOMAIN/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword123",
    "display_name": "Your Name"
  }'
```

The response includes an `access_token`. `cookies.txt` saves the `refresh_token` HttpOnly cookie.

---

# Vision

Personal AI Operating System (AI OS) is an intelligent life management platform designed to become a **second brain**.

The goal is to eliminate the need for multiple disconnected applications by providing a unified platform for productivity, learning, finance, running, journaling, communication improvement, AI assistance, analytics, and life history.

Instead of using Notion, Google Keep, Google Calendar, Strava, TickTick, ChatGPT, Excel, habit trackers, notes, journals, and expense apps separately — everything should live in one connected ecosystem.

The application should continuously learn from personal data and provide intelligent recommendations based on history, goals, and current progress.

---

# Product goals

Help become better every day across:

- Productivity
- Career growth & backend engineering
- AI learning
- Communication improvement
- Running & marathon preparation
- Finance
- Personal growth, journaling & knowledge management
- Decision making

---

# Core philosophy

This is **not** a todo app, note app, or habit tracker.

This is an **operating system for life.**

Everything inside should be connected — for example sleep → mood → productivity → learning → career, or running → health → confidence → communication → interviews → career opportunities. AI should identify these relationships automatically.

---

# Design philosophy

## Simplicity first

Prefer professional desktop-software density over decorative UI.

**Inspiration:** VS Code, IntelliJ, GitHub, pgAdmin, Jira  

**Avoid:** glassmorphism, heavy shadows, large gradients, unnecessary animation  

**Use:** compact layout, keyboard-friendly navigation, lightweight components, fast paths  

Functionality always beats appearance.

---

# Primary principles

The application must be:

- Fast & reliable
- Offline first
- AI powered
- Mobile & desktop friendly
- Installable (PWA)
- Secure
- Easy to maintain

---

# Offline first

Internet should never be a hard requirement. Offline, the user can still create tasks, update goals, complete habits, write journals, add expenses, log runs, and upload metadata.

When connectivity returns, sync happens automatically via a queue — the user only sees “Syncing…” then “Everything is up to date.”

---

# AI philosophy

AI must not behave like a generic chatbot. Prefer answering from personal data: goals, tasks, journals, running, finance, learning, career, Q&A, communication notes, documents, and prior AI conversations. Use general knowledge only when personal data is unavailable.

---

# Product modules

| Area | Includes |
|------|----------|
| Foundation | Auth, dashboard, profile, settings, notifications |
| Productivity | Goals, tasks, habits, calendar, journal, knowledge notes, timeline |
| Running | Practice sessions, marathon goals, races, PBs, history |
| Learning | Books, courses, certifications, coding practice, study sessions |
| Career | Resume, projects, interview prep, applications, GitHub progress |
| Communication | Vocabulary, writing/speaking practice, mock interviews |
| Finance | Income, expenses, savings, investments, loans, financial goals |
| Personal growth | Wishlist, bucket list, personal Q&A, life timeline, memories |
| AI | Assistant, daily/weekly/monthly reviews, domain coaches |
| Analytics | History, stats, charts, insights, achievements, recommendations |

---

# Storage philosophy

Large files should not live in PostgreSQL.

- **PostgreSQL / SQLite:** metadata, references, relationships  
- **Object storage (S3 or local uploads in alpha):** images, PDFs, certificates, OCR docs, resumes, reports  

---

# Synchronization philosophy

Every create / update / delete is stored locally, shown immediately, queued for sync, then marked complete when the server confirms. The UI should never feel blocked by the network.

---

# Performance philosophy

Target: instant UI — lazy loading, background sync, API caching, optimistic updates, virtual lists, pagination, and a small bundle. The product should feel like native desktop software.

---

# Telegram integration

Telegram is a **built-in companion channel** (not just a plan). How to use it: [docs/TELEGRAM_BOT_GUIDE.md](docs/TELEGRAM_BOT_GUIDE.md). Setup details: [docs/TELEGRAM_NOTIFIER.md](docs/TELEGRAM_NOTIFIER.md).

**What works today**

- Encrypted bot token + chat id per user
- Event push on create (tasks, running, calendar, habits, goals / milestones) via domain events + transactional outbox
- Per-event `notify_on` toggles and scheduled digests (daily/weekly, timezone-aware)
- Two-way commands: `/help`, `/tasks`, `/today`, `/done <id>`, `/habits`, `/goals`
- Webhook on HTTPS (`PUBLIC_BASE_URL`) or long-polling in local/dev
- Integrations UI: credentials, notify-on, digest schedule, webhook register/status, test & manual digest

**Planned / not yet**

- Natural-language quick capture (“Expense 320 Lunch”, “Ran 12km…”) as free-form parsing
- AI chat over Telegram

---

# Export philosophy

Important data should be exportable (PDF, CSV, Excel, JSON) — running, finance, learning, life summary, year review, AI progress, resume timeline.

---

# Integrations

Modular integrations, independently enableable:

| Status | Integration |
|--------|-------------|
| ✅ Built | Telegram bot (notify, commands, digests) |
| Planned | GitHub, Google Calendar, Google Fit / Apple Health / Garmin / Strava |
| Optional / planned | OpenAI, Gemini, email, OCR services |

---

# Long-term goal

Five years from now this application should hold every goal, achievement, journal, run, marathon, expense, resume, interview, book, course, AI conversation, dream, and memory — the single app opened every morning and closed last at night.
