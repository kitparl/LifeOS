# Feature Implementation Prompt

You are working on my application. Please implement the following features and improvements with a strong focus on **clean architecture, reusability, scalability, and mobile-first responsive design**.

## General Engineering Principles

* Do **not** implement quick fixes or one-off solutions.
* Build reusable components that can be used across multiple modules in the future.
* Follow existing project architecture and coding standards.
* Keep the UI modern, polished, and consistent.
* Ensure everything works properly on **mobile web, tablet, and desktop**.
* Think long-term. If a feature can become reusable, create it as a shared component/service instead of coupling it to a single module.

---

# 1. Running Module

## Events & Competition → Calendar Sync

Implement a **two-way synchronization** between the Running module and Calendar.

### Requirements

* Whenever a new Event or Competition is created, it should automatically appear in the Calendar.
* Editing the event from the Running module should update the Calendar.
* Editing the event directly from the Calendar should also update the Running module.
* Deleting from either side should remain synchronized.
* Avoid duplicate entries.
* Preserve a single source of truth.

### Architecture

Instead of directly connecting Running → Calendar, introduce a reusable abstraction.

For example:

* Shared Event Service
* Common Event Model
* Central Scheduling Layer
* Shared Calendar Entity

The goal is that future modules (Tasks, Study Planner, Travel, etc.) can also integrate with this same scheduling system without additional custom logic.

Think of this as a reusable scheduling infrastructure rather than a Running-specific implementation.

---

# 2. Journal Module

## New Entry Experience

The current UI feels like a basic form.

I want it to feel like writing in a real diary or journal.

### Layout

Rework the page into a writing-focused experience.

Suggested flow:

* Title
* Date
* Main content editor (largest section)
* Gratitude
* Wins
* Lessons Learned (always shown last)

---

## Markdown Editor

Replace the current content field with a full Markdown editor.

Requirements:

* Live editing experience
* Markdown support
* Clean typography
* Comfortable writing layout
* Large writing area
* Auto resize
* Keyboard friendly
* Mobile friendly

### Reusability

Do **not** make this Journal-specific.

Create a reusable Markdown Editor component so it can later be used in:

* Notes
* Documentation
* Knowledge Base
* Project documentation
* Book summaries
* Learning module
* Any future content editor

---

## Journal UI

The writing experience should feel similar to modern note-taking apps.

Focus on:

* minimal distractions
* beautiful spacing
* comfortable typography
* immersive writing experience
* responsive design

It should feel like writing inside a premium journal instead of filling out a form.

---

# 3. Personal Q&A Module

Introduce a new **Type** field.

Examples:

* Tech
* Learning
* Life
* Lesson
* Thought
* Career
* Business
* Personal
* Ideas

Requirements

* User can select existing types.
* User can create custom types.
* Custom types become reusable later.
* Type system should be extensible.

Do not hardcode the values.

---

# 4. Communication Module

## Vocabulary / Writing / Speaking

### Light Mode Bug

Currently text becomes white on a white background in light mode.

Fix all theme-related color issues.

Verify:

* Light mode
* Dark mode
* Hover
* Focus
* Disabled states

Ensure accessibility and proper contrast.

---

## Writing Popup Bug

Current issue:

* After enlarging/maximizing the writing popup, it cannot be closed.

Fix the popup lifecycle completely.

Verify:

* Open
* Resize
* Maximize
* Restore
* Close
* Escape key
* Mobile interaction

---

# 5. New Module — Knowledge Notes

Create a brand-new module for structured Markdown-based knowledge management.

This should behave like a personal knowledge notebook.

## Purpose

Store notes for subjects such as:

* Mathematics
* Physics
* AI
* Machine Learning
* Programming Languages
* System Design
* Books
* Research
* Personal Learning
* Any future subject

---

## Suggested Hierarchy

```
Subject

 ├── Description

 ├── Chapters

 │      ├── Chapter Description

 │      ├── Sections

 │      │      ├── Heading

 │      │      ├── Subheading

 │      │      ├── Markdown Content

 │      │      ├── Images

 │      │      ├── Code Blocks

 │      │      ├── Tables

 │      │      └── Links
```

The hierarchy should be flexible rather than fixed.

---

## Features

Support:

* Markdown
* Nested headings
* Code blocks
* Images
* Tables
* Lists
* Checklists
* Links
* Search
* Future tagging support
* Future backlinks support
* Future graph support (optional architecture preparation)

---

## Architecture

This module should be designed so that it can later evolve into a complete personal knowledge base.

Avoid rigid data models.

Design for extensibility.

---

# 6. Mobile Responsiveness

This is a high priority.

Every page, popup, modal, editor, table, sidebar, and form must be fully responsive.

Verify across:

* Mobile browsers
* Tablets
* Small laptops
* Desktop

Pay special attention to:

* spacing
* typography
* overflow
* touch interactions
* keyboard handling
* modal sizing
* editor usability
* navigation
* scrolling behavior

Nothing should break on smaller screens.

---

# 7. Reusability & Shared Components

Wherever possible, extract reusable building blocks instead of module-specific implementations.

Examples include:

* Markdown Editor
* Event Sync Service
* Modal System
* Tag/Type Selector
* Rich Form Components
* Note Layout Components
* Shared Editor Toolbar
* Responsive Layout Utilities

Design these as reusable shared components for future modules.

---

# 8. Expected Outcome

After implementation, the application should have:

* A reusable shared scheduling infrastructure.
* Seamless two-way Calendar synchronization.
* A premium journal writing experience.
* A reusable Markdown editor.
* Extensible Personal Q&A categorization.
* Fixed Communication module UI and popup issues.
* A scalable Knowledge Notes module.
* Excellent mobile responsiveness across the application.
* Clean, maintainable, scalable architecture with minimal technical debt.

Please think beyond simply implementing the requested features. Make thoughtful architectural decisions that improve the long-term maintainability, extensibility, and developer experience of the application while keeping the codebase clean and consistent.
