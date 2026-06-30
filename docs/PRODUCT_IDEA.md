# Personal AI Operating System (Final Product PRD)

> Build a **Personal AI Operating System** that becomes my single source
> of truth for life, productivity, career, running, finance, learning
> and AI. This is **not** a todo app. It is my second brain.

------------------------------------------------------------------------

# Product Vision

Create a fast, offline-first, AI-powered platform that combines the best
ideas from productivity, journaling, knowledge management, analytics and
personal coaching.

The application must: - Work as a desktop web application and
installable PWA. - Feel like native software. - Be extremely fast. - Be
simple instead of fancy. - Store complete history forever. - Use AI
grounded in my own data.

------------------------------------------------------------------------

# Design Philosophy

## PRIORITY

Functionality \> Beauty

Speed \> Animations

Information Density \> Empty Space

Keyboard Friendly \> Mouse Only

### UI Inspiration

-   Windows XP
-   VS Code
-   IntelliJ IDEA
-   GitHub
-   pgAdmin
-   Jira

Avoid: - Glassmorphism - Heavy gradients - Large shadows - Fancy
animations - Slow transitions

Use: - Clean typography - Compact layouts - Minimal colors - Fast
rendering - Responsive mobile layout - Dark & Light mode

------------------------------------------------------------------------

# Tech Stack

## Frontend

-   Angular (standalone components, latest stable)
-   TypeScript
-   Tailwind CSS
-   Spartan UI (shadcn-like, minimal)
-   Angular signals + services
-   @tanstack/angular-query
-   Angular Reactive Forms
-   Zod
-   Minimal CSS transitions (max 200ms)
-   Dexie.js (IndexedDB)
-   Angular service worker (@angular/pwa)
-   Workbox
-   ngx-charts / ECharts
-   FullCalendar (Angular)
-   Leaflet + OpenStreetMap

## Backend

-   FastAPI
-   SQLAlchemy 2
-   Alembic
-   Pydantic
-   PostgreSQL
-   Redis

## AI

-   OpenAI / Gemini
-   LangChain
-   LangGraph
-   pgvector
-   RAG

## Storage

-   Amazon S3
-   PostgreSQL stores metadata only.

------------------------------------------------------------------------

# Core Dashboard

Dashboard is command center.

Include:

-   AI Chat (always visible)
-   Today's Tasks
-   Today's Habits
-   Goal Progress
-   Running Goal Progress
-   Finance Summary
-   Learning Summary
-   Recent Journals
-   Calendar Preview
-   Notifications
-   Pending Offline Sync
-   Quick Add
-   Search Everywhere
-   AI Daily Recommendation

------------------------------------------------------------------------

# AI Assistant

Must answer ONLY using relevant personal context whenever possible.

Workflow:

Question → Detect Intent → Retrieve relevant database records → Retrieve
documents → Retrieve embeddings → Build context → Generate answer

Capabilities: - Daily Planner - Weekly Review - Monthly Review - Year
Review - Running Coach - Finance Advisor - Career Coach - Learning
Coach - Productivity Coach - Communication Coach - Goal Planner - Habit
Analysis - Pattern Detection - Predictive Suggestions

Never dump entire database into prompt.

------------------------------------------------------------------------

# Modules

## Goals

Life, Career, Running, Finance, Learning and Personal goals.

Features: - hierarchy - milestones - subtasks - attachments - notes -
reminders - AI suggestions - history - completion timeline

## Tasks

Recurring tasks, dependencies, priorities, tags, due dates, attachments,
reminders, history and offline editing.

## Habits

Track streaks, trends, missed days, completion percentage and AI
correlation.

## Running Goals

Purpose: Training and race planning.

Track: - Marathon Goal - Half Marathon Goal - Practice Sessions - Target
Time - Target Pace - Practice Time - Practice Distance - Weather - Notes

Race Events: - Register manually - Upcoming - Completed - Cancelled -
Medal - Bib Number - Certificate - Photos - Result

Personal Best: - 5K - 10K - 15K - Half Marathon - 30K - Marathon

Maintain complete PB history.

## Learning

Books, courses, certifications, videos, coding, interview prep, study
plans and AI recommendations.

## Career

Resume versions, projects, GitHub summary, interviews, job applications,
achievements and portfolio.

## Finance

Income, expenses, budgets, savings, investments, loans, recurring
payments and financial goals.

## Journal

Morning plan, night reflection, gratitude, wins, failures, lessons,
attachments and AI summaries.

## Mood

Stress, confidence, motivation, happiness and trends.

## Calendar

Unified calendar for tasks, workouts, bills, interviews and recurring
events.

## Communication Improvement

Vocabulary: - word - meaning - examples - pronunciation - synonyms -
revision - mastery

Writing: - blogs - essays - LinkedIn - interview answers - notes

AI feedback: - grammar - clarity - tone - readability - confidence

Speaking: - HR questions - Technical questions - Elevator pitch - Mock
interview

Track improvement history.

## Personal Q&A

Personal knowledge base.

Examples: - Why am I building this? - What motivates me? - What is
success? - Biggest mistakes? - Life lessons?

Every answer: - version history - AI summary - linked journals - linked
goals

## Wishlist / Bucket List

Store dreams and ambitions.

Each item: - title - category - target date - estimated cost - notes -
checklist - progress - attachments

Dream Gallery: Store photos/videos/documents in Amazon S3.

Examples: - Japan Trip - Buy House - Full Marathon - Learn Japanese

## Life Timeline

Chronological history of life.

Include: - goals - achievements - runs - journals - finances -
certificates - photos - AI milestones

------------------------------------------------------------------------

# Storage (Amazon S3)

Use S3 for: - Profile images - Bucket list photos - Goal attachments -
Journal images - Running photos - Marathon certificates - Medals -
Resume PDFs - Reports - Bills - OCR uploads - Documents

------------------------------------------------------------------------

# Search

Global search: - goals - journals - AI chats - runs - finance -
vocabulary - Q&A - files

Support semantic search.

------------------------------------------------------------------------

# Telegram Integration

Integrate Telegram Bot.

Features: - Morning briefing - Evening summary - Weekly AI review -
Habit reminders - Expense quick add - Run quick add - Journal quick
add - AI chat - Notifications

Examples: Expense 250 Lunch Ran 10km in 55m

------------------------------------------------------------------------

# Offline First

Requirements: - IndexedDB local storage. - Instant UI updates. - Queue
all unsynced actions. - Automatic sync when online. - Conflict
resolution. - Sync status indicator. - Manual retry. - Works fully
offline. - Mobile-first synchronization.

------------------------------------------------------------------------

# Reports & Export

Everything exportable.

Formats: - PDF - CSV - Excel - JSON

Reports: - Daily - Weekly - Monthly - Yearly - AI Progress Report -
Running Report - Finance Report - Learning Report - Habit Report -
Complete Life Report - Resume Achievement Timeline

------------------------------------------------------------------------

# Performance Requirements

-   Fast startup
-   Lazy loading
-   Code splitting
-   Optimistic UI
-   Background sync
-   API caching
-   Pagination
-   Virtualized lists
-   Small bundle size

Target: Application should feel instant.

------------------------------------------------------------------------

# Integrations

-   GitHub
-   Google Calendar
-   Google Fit
-   Apple Health
-   Strava
-   Garmin
-   OCR
-   Voice Commands

------------------------------------------------------------------------

# Final Goal

This application should become the only application I need to manage my
life. It should continuously learn from my data, preserve my complete
history, provide AI-powered insights, synchronize seamlessly across
devices, work offline, integrate with Telegram, store rich media in
Amazon S3, and help me make better decisions every day.
