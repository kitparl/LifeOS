# ⚙️ TECH STACK & ENGINEERING STANDARDS

> Personal AI Operating System (AI OS)

Version: 1.0

Status: Technical Specification

---

# Purpose

This document defines the official technology stack and engineering standards for the Personal AI Operating System.

Every future feature must follow these standards.

Technology decisions should prioritize:

- Long-term maintainability
- Performance
- Simplicity
- Scalability
- Developer Experience
- AI Integration
- Offline Support

Technology should never be selected because it is trendy.

---

# Engineering Philosophy

The application should be built like a professional SaaS product.

It should be easy to:

- Maintain
- Test
- Scale
- Extend
- Deploy
- Debug

The architecture should remain clean even after years of development.

---

# Overall Stack

Frontend

↓

Angular

↓

FastAPI

↓

PostgreSQL

↓

Amazon S3

↓

AI Services

This architecture must remain modular.

Every layer should be replaceable.

---

# Frontend

Framework

Angular (Latest Stable, standalone components)

Reason

- Mature enterprise framework
- Excellent TypeScript support
- Built-in routing, forms, HTTP, PWA
- Strong structure for large long-term apps
- Signals for reactive state

---

Language

TypeScript

Reason

Type safety

Better IDE support

Better refactoring

Reduced runtime bugs

Mandatory.

No plain JavaScript.

---

Styling

Tailwind CSS

Reason

- Lightweight
- Utility First
- Fast Development
- Easy Maintenance

Rules

Avoid

Large custom CSS

Massive component libraries

Heavy animations

Use

Utility classes

Reusable components

Minimal custom CSS

---

Component Library

Spartan UI (+ Tailwind CSS)

Reason

shadcn-like approach for Angular

Unstyled/minimal primitives

Easy customization

Minimal runtime overhead

---

Icons

Lucide Angular

Reason

Simple

Modern

Lightweight

Consistent

---

State Management

Angular signals + injectable services

Reason

Built-in, simple, fast

No unnecessary boilerplate

Global UI state only

Do not duplicate server state here

---

Server State

@tanstack/angular-query

Reason

Caching

Background updates

Retry

Synchronization

Offline support

Pagination

Optimistic updates

All API requests should use TanStack Query or HttpClient services with consistent patterns.

---

Forms

Angular Reactive Forms

Reason

Built-in, fast

Excellent validation support

Works with Zod for shared schemas

---

Validation

Zod

Reason

Type-safe validation

Reusable schemas

Frontend + Backend consistency

---

Charts

ngx-charts or ECharts

Reason

Simple

Responsive

Lightweight

Readable

Avoid complex chart libraries.

---

Calendar

FullCalendar (Angular wrapper)

Reason

Professional

Reliable

Recurring events

Drag and Drop

---

Maps

Leaflet

OpenStreetMap

Reason

Free

Lightweight

No Google Maps costs

Use only where maps provide real value.

---

PWA

@angular/pwa (service worker)

Workbox

Requirements

Offline

Caching

Installable

Background synchronization

App-like behavior

---

Offline Database

IndexedDB

Library

Dexie.js

Reason

Reliable

Fast

Large storage

Supports queues

---

Backend

Framework

FastAPI

Reason

Fast

Modern

Excellent documentation

Automatic OpenAPI

Type safety

Perfect AI ecosystem

---

Language

Python

Reason

AI ecosystem

Fast development

Easy maintenance

Excellent libraries

---

Validation

Pydantic

Reason

Request validation

Response validation

Type safety

Serialization

---

ORM

SQLAlchemy 2.0

Reason

Powerful

Mature

Flexible

Supports complex relationships

---

Migration

Alembic

Reason

Database version control

Rollback support

Production ready

---

Authentication

JWT

Refresh Tokens

HTTP-only Cookies

Google OAuth

GitHub OAuth

Rules

Never store access tokens in Local Storage.

Refresh tokens should be HTTP-only.

---

Database

PostgreSQL

Reason

Reliable

Scalable

Excellent indexing

JSON support

Full-text search

Extensions

Production ready

---

Vector Search

pgvector

Reason

Semantic Search

AI Memory

RAG

Embeddings

---

Cache

Redis

Uses

Caching

Rate Limiting

Background Jobs

Temporary Storage

Session Support

Future Queue System

---

File Storage

Amazon S3

Purpose

Profile Images

Journal Images

Certificates

Reports

Bucket List Photos

Resume PDFs

OCR Files

Running Photos

Documents

Rules

Never store large files in PostgreSQL.

Store only

URL

Metadata

Relationships

---

AI

Architecture

Provider Agnostic

Supported Providers

OpenAI

Gemini

Future providers should be easy to add.

Never hardcode provider logic.

---

AI Framework

LangChain

Reason

RAG

Prompt Pipelines

Memory

Tool Calling

Context Management

---

Workflow Engine

LangGraph

Reason

Multi-step AI workflows

Planning

Decision making

Agent orchestration

---

Embedding Storage

pgvector

Purpose

Semantic Search

Knowledge Retrieval

AI Context

---

Notifications

Telegram Bot

Email

Push Notifications

Future

Slack

Microsoft Teams

Discord

---

Search

Keyword Search

PostgreSQL Full Text Search

Semantic Search

pgvector

Hybrid Search

Keyword + AI

Every searchable module should support both.

---

Reports

Generate

PDF

CSV

Excel

JSON

Reports should be generated on demand.

Support scheduled reports in future.

---

Development Environment

IDE

VS Code

Cursor

Docker Desktop

Git

GitHub

Local PostgreSQL

---

Version Control

Git

Branch Strategy

main

development

feature/*

bugfix/*

release/*

hotfix/*

Never commit directly to main.

---

Environment Variables

Separate

Development

Testing

Production

Never commit secrets.

---

API Design

REST First

JSON

Versioned

/api/v1/

Future

WebSockets

Streaming AI

---

Folder Organization

Every module should follow the same pattern.

Example

goal/

api/

service/

repository/

schema/

model/

validator/

tests/

This structure must remain consistent.

---

Coding Standards

Backend

PEP8

Type hints everywhere

Small functions

Single responsibility

No duplicated logic

Frontend

Strict TypeScript

Standalone components

Reusable components

No inline business logic in templates

Services and signals for state

Shared utilities

---

Testing

Backend

pytest

Frontend

Jasmine (or Vitest)

Playwright

Testing should be added for every major feature.

---

Logging

Structured logging

Request IDs

Error IDs

Audit logs

Do not use print() in production.

---

Monitoring

Error Tracking

Performance Monitoring

API Monitoring

Health Checks

---

Security

HTTPS only

Rate Limiting

CSRF Protection

Input Validation

Output Validation

Encryption

Secure Cookies

Least Privilege

---

Performance Goals

Dashboard

<2 seconds

Page Navigation

<200ms

Search

<150ms

AI Response

Streaming

Large Lists

Virtualized

Background Sync

Automatic

Offline Ready

Yes

---

Dependency Rules

Before adding any dependency ask:

Can existing code solve this?

Is it actively maintained?

Does it increase bundle size significantly?

Is it production ready?

Does it simplify development?

If the answer is "No", do not add it.

Keep dependencies minimal.

---

Scalability

The application should support:

100 users

1,000 users

10,000 users

without requiring architectural changes.

Even though this starts as a personal project, it should be designed like a SaaS product.

---

Final Engineering Principle

Choose boring, reliable technology over exciting, experimental technology.

The goal is to build software that is still easy to maintain five years from now.

Stability, simplicity, and developer productivity always come before trends.