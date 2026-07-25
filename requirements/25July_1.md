IMPORTANT: Before editing any file, first determine whether a new file can achieve the same result. Prefer creating new files over modifying existing ones. Never overwrite or refactor stable production code unless explicitly instructed.

# ROLE

You are a senior Full Stack Architect working on an existing production-ready LifeOS project.

Your goal is to ADD a completely new Analytics module.

IMPORTANT:
This project is already stable.
Everything currently works.
DO NOT refactor existing code.
DO NOT modify existing business logic.
DO NOT rename files.
DO NOT move files.
DO NOT change APIs.
DO NOT change database tables unless absolutely necessary.

This is an additive feature only.

--------------------------------------------------
PRIMARY OBJECTIVE
--------------------------------------------------

Develop a complete Analytics Dashboard module that integrates into the existing application without affecting any existing functionality.

The Analytics module must be completely isolated and modular.

It should be designed so AI-powered insights can be plugged in later without requiring any major refactoring.

AI IS NOT IMPLEMENTED NOW.

Instead, create the architecture, interfaces and placeholders.

--------------------------------------------------
STRICT RULES
--------------------------------------------------

1. Existing functionality must remain untouched.

2. Never rewrite existing components.

3. Never refactor working code.

4. Never replace existing APIs.

5. Never modify authentication.

6. Never modify routing unless only ADDING new analytics routes.

7. Never change existing database schema unless adding new analytics tables is required.

8. Never delete code.

9. Never introduce breaking changes.

10. Follow existing coding style.

--------------------------------------------------
IMPLEMENTATION STRATEGY
--------------------------------------------------

Only ADD new files.

Only ADD new modules.

Only ADD new services.

Only ADD new components.

Only ADD new endpoints.

Reuse existing repositories/services whenever possible.

Analytics must read data only.

It must not modify business data.

--------------------------------------------------
NEW MODULE
--------------------------------------------------

Create

Analytics Module

containing

analytics/

    dashboard/

    goals/

    habits/

    productivity/

    journal/

    ai/

--------------------------------------------------
BACKEND
--------------------------------------------------

Create Analytics Service.

Responsibilities

Aggregate data only.

Provide optimized endpoints.

Examples

/dashboard

/dashboard/productivity

/dashboard/goals

/dashboard/habits

/dashboard/journal

/dashboard/summary

Future

/dashboard/ai

(do not implement AI)

Return placeholder structure.

--------------------------------------------------
DATABASE
--------------------------------------------------

Do NOT modify existing tables.

Use existing entities.

Aggregate using queries.

If performance becomes an issue,

create separate analytics cache tables

WITHOUT changing existing models.

--------------------------------------------------
FRONTEND
--------------------------------------------------

Create new menu

Analytics

Inside Analytics

Dashboard

Goals

Habits

Productivity

Journal

AI Insights (Coming Soon)

Do not modify existing pages.

--------------------------------------------------
HOME DASHBOARD
--------------------------------------------------

Create KPI cards

Life Score

Today's Tasks

Completed Tasks

Goal Progress

Habit Score

Focus Time

Journal Streak

Mood

Upcoming Events

Recent Activity

--------------------------------------------------
PRODUCTIVITY PAGE
--------------------------------------------------

Charts

Daily Tasks

Weekly Tasks

Monthly Tasks

Task Completion

Overdue Tasks

Focus Hours

Deep Work

Category Distribution

Calendar Heatmap

--------------------------------------------------
GOAL ANALYTICS
--------------------------------------------------

Goal Progress

Velocity

Remaining Tasks

Milestones

Completion Forecast

Risk Indicator

Burndown Chart

--------------------------------------------------
HABIT ANALYTICS
--------------------------------------------------

Current Streak

Longest Streak

Consistency %

Weekly Completion

Monthly Completion

Habit Heatmap

Best Habit

Worst Habit

--------------------------------------------------
JOURNAL ANALYTICS
--------------------------------------------------

Mood Trend

Journal Frequency

Word Count

Writing Streak

Sentiment Placeholder

Emotion Placeholder

--------------------------------------------------
AI INSIGHTS
--------------------------------------------------

DO NOT IMPLEMENT AI.

Instead create

AnalyticsAIService

with interface

interface AnalyticsInsightProvider {

getDailyInsights()

getWeeklyInsights()

getMonthlyInsights()

getPredictions()

}

Return

Coming Soon

or mocked data.

Future AI implementation should only replace this service.

Nothing else.

--------------------------------------------------
CHARTS
--------------------------------------------------

Use existing chart library if present.

Otherwise use lightweight chart library already compatible with project.

Charts should be reusable components.

--------------------------------------------------
ARCHITECTURE
--------------------------------------------------

Analytics

↓

Controllers

↓

Services

↓

Aggregation Layer

↓

Existing Repositories

↓

Database

Future

AI Service

↓

Analytics Service

↓

LLM

No current dependency on AI.

--------------------------------------------------
EXTENSIBILITY
--------------------------------------------------

Every dashboard widget should implement a common interface.

Example

DashboardWidget

title

icon

type

endpoint

refreshInterval

component

This allows future drag-and-drop widgets.

--------------------------------------------------
PERFORMANCE
--------------------------------------------------

Avoid expensive queries.

Support pagination.

Support lazy loading.

Support caching.

Prepare summary endpoints.

--------------------------------------------------
SECURITY
--------------------------------------------------

Respect existing authentication.

Respect existing authorization.

Do not bypass permissions.

--------------------------------------------------
UI
--------------------------------------------------

Use the existing design system.

Match current colors.

Match spacing.

Match typography.

Do not redesign the application.

Analytics should look like it has always been part of the app.

--------------------------------------------------
FUTURE AI PLACEHOLDERS
--------------------------------------------------

Create empty interfaces for

Insight Engine

Prediction Engine

Recommendation Engine

Trend Analyzer

Pattern Detector

Each should contain TODO comments.

No AI implementation.

--------------------------------------------------
DELIVERABLES
--------------------------------------------------

For every step:

1. Explain what will be added.

2. Explain why.

3. List new files.

4. Never overwrite existing files.

5. Never modify stable code unless absolutely necessary.

6. Clearly separate new code from existing code.

--------------------------------------------------
FINAL GOAL
--------------------------------------------------

The repository should behave exactly as before.

The only visible change should be the new Analytics module.

Everything must remain backward compatible.

The codebase should be fully prepared for future AI integration without requiring architectural changes.