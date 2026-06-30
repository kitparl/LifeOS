# 🧠 Personal AI Operating System (LifeOS)

> **Version:** 1.0 (Personal Alpha)  
> **Author:** Pranshu Bisht  
> **Status:** Phase 3 Complete — ready for personal use & private Heroku deploy  
> **Architecture:** Offline First • AI Powered • Mobile Friendly • Personal Knowledge System

---

## Quick links

| Document | Purpose |
|----------|---------|
| [PHASE-1.md](docs/PHASE-1.md) | Foundation MVP (auth, goals, tasks, habits, PWA, …) |
| [PHASE-2.md](docs/PHASE-2.md) | Intelligence (AI RAG, learning, finance, analytics, …) |
| [PHASE-3.md](docs/PHASE-3.md) | Full AI OS (memory, coaches, OCR, voice, …) |
| [improvements/v1.md](improvements/v1.md) | Release readiness & what to improve before public v1.0 |
| [DEPLOY_HEROKU.md](docs/DEPLOY_HEROKU.md) | Deploy to Heroku (~$13/mo, GitHub Student) |
| [ROADMAP.md](docs/ROADMAP.md) | Original product roadmap |
| [runProject.md](runProject.md) | Run locally (dev) |

---

## Project status (June 2026)

**All 27 units delivered** (Phase 1: 0–11, Phase 2: 12–18, Phase 3: 19–26).

| Area | Status |
|------|--------|
| Feature roadmap | ✅ Complete |
| Personal / private use | ✅ Ready |
| Tests | ✅ 39 backend + 18 frontend |
| Public production release | ⚠️ See [improvements/v1.md](improvements/v1.md) |

**Not production-complete yet:** Alembic migrations, CI/CD, rate limiting, Playwright e2e, live integration OAuth, full OCR for images/PDF. Fine for personal alpha.

---

## Run locally (development)

**Backend** (port 8000):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt email-validator
cp .env.example .env   # edit SECRET_KEY, OPENAI_API_KEY optional
uvicorn app.main:app --reload --port 8000
```

**Frontend** (port 4200):

```bash
cd frontend
npm install --legacy-peer-deps
npm start
```

Open http://localhost:4200 — API at http://localhost:8000/api/v1.

---

## Deploy to Heroku

Single-app deploy: FastAPI serves the Angular build + API. Uses Heroku Postgres.

**Full guide:** [docs/DEPLOY_HEROKU.md](docs/DEPLOY_HEROKU.md)

```bash
heroku create lifeos-yourname
heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY="$(openssl rand -hex 32)" COOKIE_SECURE=true
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
git push heroku main
```

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Angular 19 (standalone), Tailwind, Dexie, PWA service worker |
| Backend | FastAPI, SQLAlchemy 2 async, Pydantic |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL (Heroku Postgres) |
| Auth | JWT + HttpOnly refresh cookie |
| AI | OpenAI (optional), local RAG index |
| Tests | pytest, Karma/Jasmine |

---

## Modules (API `/api/v1`)

**Phase 1:** auth, dashboard, goals, tasks, habits, running, calendar, journal, mood, communication, qa, wishlist, search, notifications, export, files  

**Phase 2:** ai, learning, career, finance, analytics, timeline, reports  

**Phase 3:** memory, coaches, ocr, voice, integrations, automations, predictions, life-timeline

---

# Vision

Personal AI Operating System (AI OS) is an intelligent life management platform designed to become my **second brain**.

The goal is to eliminate the need for multiple disconnected applications by providing a unified platform for productivity, learning, finance, running, journaling, communication improvement, AI assistance, analytics, and life history.

Instead of using:

- Notion
- Google Keep
- Google Calendar
- Strava
- TickTick
- ChatGPT
- Excel
- Habit Tracker
- Notes
- Journal Apps
- Expense Tracker

everything should exist inside a single connected ecosystem.

The application should continuously learn from my data and provide intelligent recommendations based on my history, goals, and current progress.

---

# Product Goals

The application should help me become better every day.

Main areas include:

- Productivity
- Career Growth
- Backend Engineering
- AI Learning
- Communication Improvement
- Running & Marathon Preparation
- Finance
- Personal Growth
- Journaling
- Knowledge Management
- Decision Making

---

# Core Philosophy

This application is **not a Todo App**.

This application is **not a Note Taking App**.

This application is **not a Habit Tracker**.

This application is an **Operating System for my life.**

Everything inside the application should be connected.

Examples:

Sleep
↓

Mood

↓

Productivity

↓

Coding Hours

↓

Learning Progress

↓

Career Growth

Similarly

Running

↓

Health

↓

Confidence

↓

Communication

↓

Interview Performance

↓

Career Opportunities

AI should identify these relationships automatically.

---

# Design Philosophy

## Simplicity First

I do not want fancy interfaces.

I prefer professional desktop software.

UI Inspiration

- Windows XP
- Visual Studio Code
- IntelliJ IDEA
- GitHub
- pgAdmin
- Jira

Avoid

- Glassmorphism
- Heavy shadows
- Large gradients
- Fancy transitions
- Unnecessary animations

Use

- Compact UI
- Information Dense Layout
- Keyboard Friendly
- Lightweight Components
- Fast Navigation

Functionality is always more important than appearance.

---

# Primary Principles

The application must be

✅ Fast

✅ Reliable

✅ Offline First

✅ AI Powered

✅ Mobile Friendly

✅ Desktop Friendly

✅ Installable (PWA)

✅ Secure

✅ Easy to Maintain

---

# Offline First Philosophy

Internet should never be a requirement.

The application should work normally even without internet.

When offline

- Create Tasks
- Update Goals
- Complete Habits
- Write Journals
- Add Expenses
- Record Running Practice
- Upload Metadata

Everything should continue working.

Whenever internet becomes available

Synchronization should happen automatically.

No manual sync required.

The user should only see

"Syncing..."

then

"Everything is up to date."

---

# AI Philosophy

AI should never behave like a generic chatbot.

Instead

AI must answer using

- Goals
- Tasks
- Journals
- Running History
- Finance
- Learning
- Career
- Personal Q&A
- Communication Notes
- Uploaded Documents
- Previous AI Conversations

If relevant personal data exists

Always use it.

Only use general knowledge when personal data is unavailable.

---

# Complete Product Modules

## Foundation

- Authentication
- Dashboard
- Profile
- Settings
- Notifications

---

## Productivity

- Goals
- Tasks
- Habits
- Calendar
- Journal
- Notes
- Timeline

---

## Running

- Practice Sessions
- Marathon Goals
- Race Events
- Personal Best
- Running History

---

## Learning

- Books
- Courses
- Certifications
- Coding Practice
- Study Sessions

---

## Career

- Resume
- Projects
- Interview Preparation
- Job Applications
- GitHub Progress

---

## Communication

- Vocabulary
- Writing Practice
- Speaking Practice
- Mock Interviews
- Grammar Improvement

---

## Finance

- Income
- Expenses
- Savings
- Investments
- Loan Tracking
- Financial Goals

---

## Personal Growth

- Wishlist
- Bucket List
- Personal Q&A
- Life Timeline
- Memories

---

## AI

- Personal Assistant
- Daily Planner
- Weekly Review
- Monthly Review
- Running Coach
- Finance Advisor
- Learning Coach
- Career Coach
- Communication Coach

---

## Analytics

Everything should be measurable.

Every module should contain

History

Statistics

Charts

Insights

Progress

Achievements

AI Recommendations

---

# Storage Philosophy

Large files should never be stored inside PostgreSQL.

PostgreSQL stores

- Metadata
- References
- Relationships

Amazon S3 stores

- Images
- PDFs
- Certificates
- Journal Images
- Running Photos
- Resume Versions
- Reports
- Bucket List Photos
- OCR Documents

---

# Synchronization Philosophy

Synchronization is one of the most important parts of the application.

Every operation should be

Create

Update

Delete

↓

Stored Locally

↓

Displayed Immediately

↓

Added To Sync Queue

↓

Automatically Synced

↓

Marked Completed

The application should never feel blocked because of the network.

---

# Performance Philosophy

Target

Instant UI

Requirements

- Lazy Loading
- Background Sync
- API Caching
- Optimistic Updates
- Virtual Lists
- Pagination
- Small Bundle Size

The application should feel similar to native desktop software.

---

# Telegram Integration

Telegram should act as a lightweight companion application.

Capabilities

- Daily Briefing
- Evening Summary
- Weekly Review
- AI Chat
- Quick Expense
- Quick Journal
- Quick Running Log
- Quick Task Creation
- Notifications

Example

Expense 320 Lunch

↓

Automatically added.

Ran 12km 1h10m

↓

Running history updated.

---

# Export Philosophy

Every important piece of data should be exportable.

Supported formats

- PDF
- CSV
- Excel
- JSON

Examples

Running Report

Finance Report

Learning Report

Life Summary

Year Review

AI Progress Report

Resume Timeline

---

# Integrations

The application should support integrations with external services wherever they provide value.

Initial Integrations

- Telegram Bot
- GitHub
- Google Calendar

Planned Integrations

- Google Fit
- Apple Health
- Garmin
- Strava
- OpenAI
- Gemini
- Email Provider
- OCR Services

All integrations should be modular so they can be enabled or disabled independently.

---

# Long Term Goal

Five years from now this application should contain

Every Goal

Every Achievement

Every Journal

Every Running Practice

Every Marathon

Every Expense

Every Resume

Every Interview

Every Book

Every Course

Every AI Conversation

Every Dream

Every Memory

Everything that represents my personal and professional growth.

This should become the single application I open every morning and the last application I close before sleeping.

---
