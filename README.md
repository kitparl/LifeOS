# LifeOS

**LifeOS is one private, AI-powered app that replaces a dozen apps you'd otherwise use to manage your life — and remembers everything for you.**

## Why this exists

Normally, your life is scattered across a pile of separate apps: Todoist for tasks, Notion for notes, a journal app, Strava for running, a spreadsheet for money, ChatGPT for questions, Google Photos, Google Keep for vocabulary, a folder for certificates... None of these apps talk to each other, and none of them actually know *you* — ChatGPT forgets who you are the moment the chat ends. Your history is fragmented across ten logins, and no single place understands the full picture.

LifeOS is the opposite: **one place** that holds your goals, habits, tasks, journal, running log, finances, learning, career progress, personal notes, and more — all connected, all searchable, all yours. Over time it becomes less of a "tracking app" and more like a digital memory of your life: every goal you set, every habit you kept or broke, every race you ran, every lesson you learned, in one continuous story instead of ten disconnected fragments.

Crucially, this isn't just a place to *store* that data — it's built AI-first, meaning the AI is meant to actually read and reason over your goals, habits, journal, and history, not just answer generic questions. Instead of you asking a generic chatbot "how do I train for a marathon," you ask LifeOS, and it already knows your run history, your recent habits, and your goals — so it can actually tell you where *you* stand, coach you on your weak areas, and eventually even proactively flag things ("your running consistency dropped this week", "you haven't practiced communication in four days") before you ask.

It's built for exactly one person to use (you), which is why it can be this personal — there's no "team plan" or generic feature set to please everyone. It's built to please one person.

## What you can actually do with it

Think of it as a private personal dashboard with a bunch of rooms, all under one roof:

- **Stay on track** — to-do tasks (with sub-tasks and reminders), daily habits, recurring routines, a calendar, and a journal for your thoughts.
- **Track your running** — log runs and races, see your personal bests, and watch progress over time.
- **Practice communication** — writing and speaking practice with AI feedback, plus a vocabulary word lab.
- **Manage money** — record income/expenses and keep an eye on budgets.
- **Keep the personal stuff somewhere safe** — a wishlist ("things I want to do/get"), a private Q&A journal, knowledge notes (with optional syncing to GitHub), and mood tracking.
- **Get AI help that actually knows your data** — ask questions and get answers grounded in your own tasks/journal/notes (not generic chatbot answers), and get writing feedback on your practice writing.
- **Get nudged on Telegram** — LifeOS can message you digests, reminders, and scheduled reports, and you can even manage tasks/habits by chatting with a Telegram bot when you're away from the app.
- **Use it like a real app, not a website** — it installs like an app on your phone or laptop (PWA) and keeps working even with a flaky connection.

## Who it's for

Right now: just you, the person running it. Registration isn't open to the public — a single admin (you) explicitly unlocks account creation when you want to add a user (e.g. yourself, or someone you trust). There's no sign-up button sitting open on the internet.

If you'd like access to the application, reach out to **pranshu.java@gmail.com**.

## How it's put together (for the curious / technical reader)

You don't need to know any of this to use LifeOS, but if you're maintaining or extending it, here's the shape of it.

| Layer | What it is |
|-------|------------|
| Frontend | Angular 19 + Tailwind, styled like a Linux desktop, works as an installable PWA |
| Backend | FastAPI (Python), async SQLAlchemy 2, Pydantic v2 |
| Database | SQLite for local dev, PostgreSQL for production |
| Auth | JWT access token + HttpOnly refresh cookie, plus an admin-only "registration gate" to control who can create accounts |
| Background jobs | APScheduler — Telegram digests, reminders, cleanup jobs |
| File storage | Local disk or S3-compatible object storage |

**Backend shape** — one folder per feature area (`tasks`, `habits`, `running`, `finance`, `journal`, …) under `backend/app/modules/`, each following the same simple flow:

```text
api.py (HTTP routes)  →  service.py (business rules)  →  repository.py (database)  →  models.py
                                       ↑
                              schemas.py (request/response shapes)
```

Shared plumbing lives in `backend/app/core/`: config/settings, the database connection, auth dependencies, JWT + password hashing, a small set of domain errors (`NotFoundError`, etc.) that map to clean JSON error responses, pagination helpers, and an in-process event bus (e.g. "task created" → notify Telegram).

Integrations (Telegram bot, GitHub sync, scheduled reports, notifications) live together under `backend/app/modules/integrations/`, split into their own sub-folders (`telegram/`, `github/`, `scheduling/`, `notifications/`, `reports/`) so each concern stays easy to find.

**A typical request:**

```text
Browser (Angular app)  →  JWT in Authorization header  →  /api/v1/<feature>
                                                              ↓
                                                     service (the actual logic)
                                                              ↓
                                                     repository (SQLAlchemy)
                                                              ↓
                                              SQLite (dev) or PostgreSQL (production)
```

## Getting started (local development)

### Backend

```bash
cd backend
python3 -m venv .venv             # Python 3.10+ (production runs 3.10)
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # ENV=dev; set SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

- API base: http://localhost:8000/api/v1
- Health check: http://localhost:8000/health
- Interactive API docs (dev only): http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm start
```

App: http://localhost:4200

### Creating the first user

Registration is locked behind an admin gate — there's no open sign-up page.

1. Set `ADMIN_GATE_EMAIL` and `ADMIN_GATE_PASSWORD_HASH` in `backend/.env` (see `.env.example` for how to generate the hash).
2. Open http://localhost:4200/register-access and log in with those admin credentials.
3. Use **Add new user** (or `/register`) while that unlock is active to create an account.

Without the admin gate configured, registration stays locked for everyone — by design.

### Running tests & lint

```bash
# Backend
cd backend
source .venv/bin/activate
pytest -q
ruff check app          # full ruff config in pyproject.toml; expected to be clean

# Frontend
cd frontend
npm run lint            # ESLint; expected to be clean (0 errors, 0 warnings)
npm run test:ci         # Karma, headless Chrome
npm run build
```

## Configuration

Key variables in `backend/.env` (see `.env.example` for the full list):

| Variable | What it controls |
|----------|-------------------|
| `ENV` | `dev` for local work; `production` when deployed |
| `SECRET_KEY` | Signs tokens/cookies — **must be a unique, non-default value in production** |
| `INTEGRATION_ENC_KEY` | Encrypts stored bot tokens/secrets — **required in production** |
| `ADMIN_GATE_EMAIL` / `ADMIN_GATE_PASSWORD_HASH` | Who is allowed to unlock account creation |
| `OPENAI_API_KEY` | Optional — powers the AI chat/coach features |
| `PUBLIC_BASE_URL` | Your public HTTPS URL, needed for Telegram webhooks |
| `TELEGRAM_POLLING_ENABLED` | Set `true` to use Telegram locally without HTTPS |
| `DATABASE_URL` | Defaults to SQLite; point it at Postgres in production if you prefer |
| `PREVIEW_CACHE_DIR` | Where converted (Office→PDF) previews are cached — keep it outside the repo, same reasoning as `UPLOAD_DIR` |

## Document Viewer

A universal preview dialog (`documentViewerService.open({ documentId })`) is available anywhere in the frontend and backs it with one set of backend endpoints (`GET /api/v1/files/{id}/preview-info`, `/preview`, `/download`) built on top of the existing Files/`FileRecord` module — there is no separate "Document" model. Office/OpenDocument formats (doc/docx/odt/rtf, ppt/pptx/odp, xls/xlsx/ods) are converted to PDF on first preview by headless LibreOffice and cached by content checksum; everything else renders natively in the browser.

**Local dev** — install LibreOffice once:

```bash
# macOS
brew install --cask libreoffice

# Debian/Ubuntu
sudo apt-get install -y libreoffice libreoffice-writer libreoffice-calc libreoffice-impress libmagic1 fonts-dejavu fonts-liberation
```

No new Python dependency was needed (the repo already sniffs file types with the pure-Python `filetype` package, not `python-magic`/`libmagic`); `pdfjs-dist` is the one new frontend dependency, lazy-loaded so it stays out of the main bundle.

**Production (VPS, bare-metal — see "Deploying" below):** this repo has no Docker setup for the backend/frontend today (only Postgres/Redis run in Docker, see `infra/docker-compose.yml`), so LibreOffice is installed directly on the VPS rather than added to a "backend image," a deliberate deviation from a container-first brief to match how this app actually deploys.

Known limitations: TIFF previews are unsupported (download-only) rather than converted to PNG, to avoid a new Pillow dependency for one rare format; wide spreadsheets paginate across pages the way LibreOffice's PDF export naturally does (no custom table view was built); the conversion single-flight lock is per-worker-process only, so with multiple uvicorn workers two workers could each convert the same document once concurrently — wasteful but not corrupting, since the cache write is atomic (temp file + rename, same pattern as local file storage).

## Project layout

```text
backend/           FastAPI application (app/core + app/modules + app/tests)
frontend/          Angular single-page app
requirements/      Feature specs and cleanup briefs (local only, gitignored)
aidlc-docs/        AI-DLC planning artifacts and summaries (local only, gitignored)
```

## Documentation

| Document | Description |
|----------|-------------|
| [runProject.md](runProject.md) | Local run commands + VPS operations cheatsheet |
| [code-quality.md](code-quality.md) | Code conventions, shared helpers, and quality gates |

## Deploying (VPS)

In production, FastAPI serves both the API and the built Angular app (from `backend/static/`), sitting behind Caddy for HTTPS, run as a systemd service (`lifeos`).

```bash
# One-time: LibreOffice for Office->PDF document previews (see "Document Viewer" above)
sudo apt-get install -y libreoffice libreoffice-writer libreoffice-calc libreoffice-impress libmagic1 fonts-dejavu fonts-liberation

# On the VPS, from the repo root:
npm run build:frontend          # builds Angular → backend/static/

cd backend
source .venv/bin/activate
pip install -r requirements.txt
# Make sure .env has: ENV=production, SECRET_KEY, INTEGRATION_ENC_KEY,
# COOKIE_SECURE=true, CORS_ORIGINS, ADMIN_GATE_*, PUBLIC_BASE_URL, PREVIEW_CACHE_DIR

sudo systemctl restart lifeos
```

Day-to-day operations (deploy script, logs, rollback): [runProject.md](runProject.md).

## License

Private / personal project. All rights reserved.
