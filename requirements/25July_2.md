# LifeOS Telegram Bot - Master Product & Engineering Specification

> This document is the single source of truth for developing the Telegram interface for LifeOS.

---

# 1. Mission

The Telegram Bot is not a standalone application.

It is a Telegram-native interface for the existing LifeOS platform.

It must reuse existing backend services and business logic.

Telegram is only responsible for:

- Presentation
- Navigation
- Conversations
- Notifications
- User interaction

Business logic must remain inside backend modules.

---

# 2. Core Principles

The bot should feel like a mobile application rather than a traditional command bot.

Principles

- Minimise typing
- Minimise slash commands
- Maximise inline interactions
- Use conversational forms
- Edit messages instead of sending new ones
- Every screen must have clear next actions
- No dead ends
- Reuse existing backend services
- Never duplicate business logic
- Refactor before rewriting
- Maintain a consistent UI across all modules

---

# 3. Architecture Rules

Before implementing any feature:

1. Audit the current codebase.
2. Identify reusable services.
3. Identify reusable repositories.
4. Identify reusable UI components.
5. Extend existing implementations where practical.
6. Avoid creating duplicate abstractions.

Telegram should contain only:

- Router
- Callback Router
- Keyboard Builder
- Message Builder
- Conversation Engine
- Navigation
- State Manager
- Notification Adapter

Business logic belongs inside backend modules.

---

# 4. Mandatory Development Workflow

Every phase must follow this workflow.

## Step 1

Audit existing implementation.

Identify reusable code.

Do not code yet.

---

## Step 2

Produce an implementation proposal.

Include

- Current architecture
- Proposed architecture
- Files to modify
- Files to create
- Risks
- Migration strategy

Wait for approval if required.

---

## Step 3

Implement only the approved phase.

Never implement future phases.

---

## Step 4

Run tests.

Refactor.

Verify acceptance criteria.

---

## Step 5

Generate a completion report containing

- Files changed
- Tests added
- Refactors performed
- Remaining technical debt
- Suggestions for next phase

---

# 5. Engineering Rules

Always

✓ reuse existing services

✓ reuse repositories

✓ reuse validation

✓ reuse notification system

✓ reuse authentication

Prefer

Refactor

over

Rewrite.

Prefer

Extend

over

Duplicate.

Never create multiple implementations of the same concept.

---

# 6. UI Rules

Every Telegram screen should include appropriate navigation.

Support

🏠 Home

⬅ Back

🔄 Refresh

Pagination where required.

Use

Inline Keyboards

Reply Keyboards

Callback Queries

Message Editing

Confirmation Dialogs

Selection Menus

Avoid unnecessary typing.

---

# 7. Conversation Engine

All multi-step workflows must use a shared Conversation Engine.

Do not create separate implementations for

Tasks

Goals

Projects

Habits

Calendar

Routines

Conversation flows should be configuration-driven.

Support

Start

Next

Back

Skip

Edit

Cancel

Confirm

Resume

Timeout recovery

---

# 8. Security

Every interaction must

Validate Telegram User ID

Validate ownership

Validate permissions

Validate callback payload

Never expose

UUIDs

Database IDs

Internal implementation details

Business data belonging to other users

---

# 9. Performance

Prefer editing messages instead of sending new ones.

Reuse keyboards.

Cache repeated lookups.

Use pagination.

Reduce Telegram API requests.

---

# 10. Definition of Done

A phase is complete only when

✓ Acceptance criteria satisfied

✓ Tests pass

✓ Existing functionality preserved

✓ No duplicated business logic

✓ Shared UI components used

✓ Shared Conversation Engine used

✓ Security verified

✓ Logging added

✓ Documentation updated

✓ Technical debt documented

---

# 11. Stop Conditions

Stop implementation immediately if

- Database schema changes are required
- Existing APIs must break
- Security concerns are discovered
- Existing services cannot support the feature
- Architectural changes affect later phases

Instead produce a proposal.

---

# 12. Implementation Roadmap

# LifeOS Telegram Interactive Bot — Full Phase Roadmap

Purpose: give Cursor (Planning Mode, AIDLC workflow) the full sequence up
front, while each phase is still proposed/designed/approved on its own —
one phase per AIDLC Inception→Construction cycle. Do not implement more
than the current phase in a single pass.

Ground rules that apply to every phase:
- Reuse existing services (`TaskService`, `CalendarRepository`, etc.). No
  business logic inside `backend/app/modules/integrations/`.
- Extend the existing `command_handler.py` / `webhook_service.py`, never fork.
- Every callback/command re-verifies Telegram user ID → account ownership.
- Never expose internal DB IDs/UUIDs in visible text; short IDs only ever
  travel inside `callback_data`.
- Each phase ships with tests before being considered done, following the
  pattern in `backend/app/tests/test_telegram_*.py`.
- Existing slash commands and the digest/notification system must keep
  working after every phase.

---

## Phase 1 — Core Interactive Infrastructure + Tasks (pilot domain)

**Goal**: prove the interactive pattern end-to-end on one domain before
spreading it everywhere.

Build:
- `keyboard_builder.py` — helpers to build `InlineKeyboardMarkup` (list
  rows, per-item action rows, pagination row, back/home row).
- `callback_router.py` — parses `callback_data` (namespaced, e.g.
  `task:done:<short_id>`, `task:page:2`), dispatches to handlers, always
  re-checks ownership before calling a service.
- Minimal conversation/state holder for multi-step flows (e.g. "add task"
  asking for title then due date) — in-memory or DB-backed, scoped small.
- Redesign `/tasks` output: numbered list, emoji status, per-task
  Done/Edit buttons, pagination, footer nav (Add / Refresh / Home).
- `/dashboard` — a small home screen with buttons: Tasks, Today, Habits,
  Goals (buttons only; those routes can reuse existing text commands under
  the hood for anything not yet redesigned).

Out of scope: calendar, automations, AI, analytics, projects, notes, search.

Exit criteria: tapping through the entire Tasks flow (list → view → done →
edit due date → back to list) never requires the user to type an ID.

---

## Phase 2 — Calendar + Habits

**Goal**: extend the same conversation engine/keyboard patterns to two more
read-heavy, lower-risk domains.

Build:
- Calendar: today/week views as button-navigable screens, event detail
  cards, "free time suggestion" as a simple read-only view (reuse existing
  service methods only — do not invent new scheduling logic here).
- Habits: today's habits with one-tap complete buttons, streak shown inline.
- Extend `/dashboard` with Calendar and Habits sections.

Exit criteria: user can check today's schedule and mark a habit complete
without typing anything.

---

## Phase 3 — Goals + Routines

**Goal**: cover the remaining "daily planning" domains.

Build:
- Goals: list, view detail (progress/milestones), mark milestone complete.
- Routines: list, view steps, mark routine done for today.
- Wire both into `/dashboard`.

Exit criteria: same tap-only standard as Phases 1–2.

---

## Phase 4 — Projects + Notes (quick capture)

**Goal**: add creation-heavy flows now that the conversation engine has
been proven on read/update flows in Phases 1–3.

Build:
- Projects: list, view, task-count/progress summary, create project
  (multi-step conversation flow).
- Notes: quick capture (plain text → note), list recent, search by keyword
  (reuses existing notes service search, not a new implementation).

Exit criteria: creating a project or capturing a note from Telegram
produces the same result as doing it from the web app.

---

## Phase 5 — Notifications & Digest Upgrade

**Goal**: bring the existing (already-working) digest/notification system
up to the same interactive standard, since it predates this UI pattern.

Build:
- Add inline action buttons to relevant push notifications (e.g. a task
  reminder gets a "Mark done" button instead of requiring `/done <id>`).
- Digest message gets section-jump buttons ("View tasks", "View calendar").

Exit criteria: no regression in delivery reliability (outbox/dispatcher
behavior unchanged); notifications become actionable, not just informational.

---

## Phase 6 — Automations + AI (assistive features)

**Goal**: expose AI/automation capabilities that already exist in the
backend, without building new AI logic in the Telegram layer.

Build:
- View/pause/resume/run automations; execution history view.
- AI: daily briefing on demand, task breakdown suggestion, natural-language
  "add task" free-text entry (parsed by existing AI service, not by Telegram
  code).

Exit criteria: AI-assisted actions still route through existing AI service
interfaces; Telegram only sends prompts/receives structured responses.

---

## Phase 7 — Analytics, Search, Attachments

**Goal**: round out the remaining read-only/utility surfaces.

Build:
- Analytics: weekly/monthly summary as a formatted card (text/simple charts
  if Telegram-renderable; otherwise a link to the web dashboard).
- Universal search across tasks/notes/projects/goals via one `/search`
  entry point with paginated results.
- Attachments: accept photo/document/voice note on a task or note, store
  via the existing attachment service.

Exit criteria: each is additive and independently shippable; skip any that
don't have a clear existing backend service to call.

---

## Phase 8 — Future / Not Yet Scoped (do not build without a fresh Phase brief)

Candidates from the original vision doc, deliberately deferred:
- Telegram Mini App, voice assistant / speech-to-text
- Group support, shared task assignment, team/workspace features
- Third-party sync (Google Calendar, Notion, Slack, GitHub, WhatsApp, etc.)
- Multi-bot / plugin architecture

Each of these should get its own Phase-N brief (same shape as Phases 1–7)
written only after Phase 7 is live and in real use — do not pre-build.

---

## How to use this file with Cursor

1. Give Cursor this file plus the Phase 1 detailed prompt as the starting
   context.
2. Let AIDLC's Inception phase (reverse engineering → requirements →
   design → units) run for **Phase 1 only**.
3. Review and approve before Construction starts.
4. After Phase 1 ships and is tested, repeat step 2–3 for Phase 2, and so on.
5. Do not let Cursor jump ahead to a later phase's build work "while it's
   in there" — flag it back to this roadmap if it tries.

This roadmap is the implementation order.

Never skip phases.

Never implement multiple phases together.

Complete each phase before proceeding.

---

# 13. Cursor Instructions

Before writing any code

Read this entire document.

Audit the project.

Understand existing architecture.

Do not assume anything.

Do not duplicate code.

During implementation

Think like a senior software architect.

Continuously look for opportunities to improve the architecture while preserving behaviour.

If existing code can be refactored instead of replaced, prefer refactoring.

If reusable abstractions can be introduced without increasing complexity, introduce them.

The objective is not merely to complete the current phase.

The objective is to leave the codebase cleaner, more maintainable, and more consistent after every phase.

At the end of each phase

Produce

- Summary
- Files changed
- Tests added
- Architectural improvements
- Remaining work
- Recommendations for the next phase

Then stop.