# Improve Chapter & Section Editing Experience

Please update the existing chapter/section management UI and behavior based on the following requirements. **Do not break any existing functionality.** Keep the current design language and UI consistent with the existing application.

## 1. Make the Subject/Class Title Editable

In the first screenshot, the title currently appears as **“adfas”** and I am unable to edit it.

* Make the title editable.
* I should be able to rename **“adfas” → “AI Masterclass”** directly from the UI.
* The updated name must persist after refresh/navigation.
* Use the existing edit/save interaction pattern if one already exists in the application.

## 2. Search Notes by Chapter / Section

In the screenshot with the red arrow, add a search functionality for notes/content.

The search should:

* Allow me to search across notes/content.
* Show results grouped or clearly associated with their **Chapter → Section**.
* Make it easy to identify where each matching note/content exists.
* Clicking a search result should navigate directly to the relevant chapter and section.
* Search should work across all chapters and sections, not only the currently open chapter.

Example:

`Search: "machine learning"`

Results:

* Chapter 2 — AI Fundamentals

  * Section 3 — Machine Learning Basics
* Chapter 5 — Deep Learning

  * Section 1 — Neural Networks

## 3. Collapse / Expand Chapters

In the left sidebar where all chapters and sections are displayed:

* Make each **chapter collapsible/expandable**.
* When I click a chapter, its sections should expand underneath it.
* Clicking the chapter again should collapse its sections.
* The expanded/collapsed state should be intuitive and visually clear.
* Ideally, preserve the user's collapse/expand state while navigating within the subject.

Example:

**Chapter 1 — Introduction** ▼
   Section 1
   Section 2
   Section 3

**Chapter 2 — AI Fundamentals** ▶

When Chapter 2 is clicked:

**Chapter 2 — AI Fundamentals** ▼
   Section 1
   Section 2
   Section 3

## 4. Remember the Last Edited / Visited Section

When I return to an existing chapter, **do not automatically open the first section**.

Instead:

* Remember the last section I was working on/viewing within that chapter.
* When I revisit that chapter, automatically navigate to that last relevant section.
* This should work even when a chapter contains many sections.

Example:

Chapter 10 contains 10 sections.

I was last working on:

`Chapter 10 → Section 8`

When I leave and later open Chapter 10 again, it should automatically open:

`Chapter 10 → Section 8`

instead of Section 1.

Persist this state appropriately so normal navigation/refresh does not unexpectedly reset it.

## 5. Add Chapter/Section Close Functionality + Read Mode

Add functionality to **close a chapter/section** when I have finished working on it.

The important behavior is:

* I should be able to mark a chapter or section as **Closed/Completed**.
* Closed content should remain accessible.
* When I later open an existing/closed chapter or section, it should open in **Read Mode by default**.
* I should still have an obvious option to switch from Read Mode → Edit Mode when I want to make changes.
* New content that I am actively creating/editing can continue to open in Edit Mode.

Suggested behavior:

**Existing content**
→ Open in **Read Mode**

**Newly created content**
→ Open in **Edit Mode**

**Closed content**
→ Open in **Read Mode**

This should prevent accidental editing of completed content.

## 6. Stop Opening Everything in Edit Mode

This is the most important UX issue.

Currently, whenever I visit a subject, **everything appears to be in Edit Mode**, which makes the experience confusing and uncomfortable.

Change the default behavior so that:

### Existing content

* Open in **Read Mode**.
* Do not automatically activate editors for every section.
* Do not make every chapter/section look editable when I am simply browsing/reading.

### New content

* Open in **Edit Mode** when appropriate.
* New sections/chapters should still provide the convenient editing experience.

### Explicit editing

* I should enter Edit Mode only when I intentionally click an **Edit** action.
* After saving, return to Read Mode unless there is a good reason to remain in Edit Mode.

## Overall UX Goal

The overall experience should feel like a **content management / learning system**, not like a page where every piece of content is permanently being edited.

Desired flow:

**Open Subject**
→ See chapters in sidebar
→ Chapters are collapsed/expandable
→ Select a chapter
→ Open the last visited/edited section
→ Existing content opens in **Read Mode**
→ Search can find notes by Chapter/Section
→ Click **Edit** only when I want to modify content
→ Save changes
→ Return to **Read Mode**
→ Optionally mark chapter/section as **Closed/Completed**

## Acceptance Criteria

Please verify all of the following after implementation:

* [ ] Subject/class title can be edited and saved.
* [ ] “adfas” can be changed to “AI Masterclass”.
* [ ] Notes/content can be searched globally.
* [ ] Search results clearly show Chapter and Section.
* [ ] Clicking a search result opens the correct content.
* [ ] Chapters can be collapsed and expanded.
* [ ] Sections appear underneath their respective chapters.
* [ ] Last visited/edited section is remembered per chapter.
* [ ] Returning to a chapter opens the remembered section instead of always opening Section 1.
* [ ] Chapters/sections can be marked Closed/Completed.
* [ ] Existing content opens in Read Mode by default.
* [ ] Closed content opens in Read Mode.
* [ ] New content can still open directly in Edit Mode.
* [ ] Edit Mode requires an intentional user action for existing content.
* [ ] Saving existing content returns it to Read Mode.
* [ ] Refreshing or navigating away does not unexpectedly reset the state.
* [ ] Existing functionality and data are preserved.
* [ ] UI remains consistent with the current application's design.

Before implementing, inspect the existing component structure, state management, routing, and persistence logic. Reuse existing patterns where possible rather than introducing unnecessary new architecture.