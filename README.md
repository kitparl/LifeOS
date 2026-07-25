# LifeOS

Personal life-management platform: goals, habits, running, journal, finance, calendar, AI assistant, and Telegram companion — in one place.

## Features

- **Productivity** — goals, tasks, habits, routines, calendar, journal
- **Running** — practice logs, races, PBs
- **Learning & career** — courses, projects, interview prep
- **Finance** — income, expenses, savings tracking
- **Personal** — wishlist, Q&A, knowledge notes, mood
- **AI** — personal-data RAG chat, coaches, insights (optional OpenAI)
- **Telegram** — event notifications, digests, two-way bot commands
- **PWA** — installable, offline-friendly UI

## Tech stack

| Layer | Stack |
|-------|--------|
| Frontend | Angular 19, Tailwind CSS, PWA |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic |
| Database | SQLite (dev), PostgreSQL (production) |
| Auth | JWT access token + HttpOnly refresh cookie |
| Scheduling | APScheduler |

## Requirements

- Python 3.11+
- Node.js 20+
- Optional: OpenAI API key (AI features), Telegram bot token

## Getting started

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt email-validator
cp .env.example .env               # set SECRET_KEY; optional OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000/api/v1  
- Health: http://localhost:8000/health  
- OpenAPI docs (dev): http://localhost:8000/docs  

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm start
```

App: http://localhost:4200

### Create a user

Registration is API-only (not exposed in the UI):

```bash
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword123","display_name":"Your Name"}'
```

## Configuration

Key variables in `backend/.env`:

| Variable | Description |
|----------|-------------|
| `ENV` | `dev` for local; `production` for deploy |
| `SECRET_KEY` | JWT / crypto secret |
| `INTEGRATION_ENC_KEY` | Fernet key for encrypted bot tokens |
| `OPENAI_API_KEY` | Optional — AI features |
| `PUBLIC_BASE_URL` | Public HTTPS API URL (Telegram webhooks) |
| `TELEGRAM_POLLING_ENABLED` | `true` for local Telegram without HTTPS |

See `backend/.env.example` for the full list.

## Documentation

| Document | Description |
|----------|-------------|
| [runProject.md](runProject.md) | Local run notes |
| [docs/DEPLOY_HEROKU.md](docs/DEPLOY_HEROKU.md) | Heroku deployment |
| [docs/SSL_CADDY.md](docs/SSL_CADDY.md) | HTTPS / Caddy reverse proxy |
| [docs/TELEGRAM_BOT_GUIDE.md](docs/TELEGRAM_BOT_GUIDE.md) | Telegram user guide |
| [docs/TELEGRAM_NOTIFIER.md](docs/TELEGRAM_NOTIFIER.md) | Telegram engineer setup |
| [docs/SCHEDULED_REPORTS.md](docs/SCHEDULED_REPORTS.md) | Scheduled reports & reminders |
| [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md) | Product vision |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Roadmap |
| [requirements/v1.md](requirements/v1.md) | Pre–public-release checklist |

## Deploy

Single Heroku app (API + Angular build + Postgres):

```bash
heroku create lifeos-yourname
heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY="$(openssl rand -hex 32)" COOKIE_SECURE=true ENV=production
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
git push heroku main
```

Full steps: [docs/DEPLOY_HEROKU.md](docs/DEPLOY_HEROKU.md).

## Project layout

```
backend/     FastAPI application
frontend/    Angular SPA
docs/        Guides and design docs
requirements/ Release notes and checklists
```

## License

Private / personal project. All rights reserved.
