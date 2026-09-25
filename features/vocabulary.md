# Feature: Vocabulary Learning & Communication Module

LifeOS can teach you English vocabulary from a structured 15,000-item dataset: a new set of 10 words every day, with bookmarks, unlimited personal examples, revision, a progress dashboard, and 7 vocabulary games. This document is the full feature reference (data import, daily learning rules, all sub-features, API reference, and architecture).

---

## Overview

| Capability | Description |
|------------|--------------|
| **Daily learning** | 10 new words/day, gated on IST midnight + explicit "Accept"; manual "Next Set"; per-word "Change" |
| **No repetition** | A word is never assigned as *new* vocabulary to the same user twice, ever |
| **Bookmarks** | Bookmark/unbookmark any word; never affects the daily sequence |
| **Personal examples** | Unlimited user-written example sentences per word; never overwrites the master example |
| **History** | Every daily/manual set ever shown, grouped by date, reflecting actual changes made |
| **Progress dashboard** | Learned count (dynamic denominator), current level, streak, bookmarks, needs-revision count |
| **Search & Library** | Server-side search/filter over the full dataset (term, level, type, topic) |
| **Revision** | Re-practice already-learned words from 8 sources — never consumes new vocabulary |
| **Games** | 7 game types (meaning/synonym/antonym quiz, fill-in-blank, example completion, word/meaning matching) — never consumes new vocabulary |
| **Import pipeline** | Idempotent CLI importer for the source JSON dataset, run manually, never at app startup |

The daily-sequencing logic (who gets which word next, and only once) is the highest-risk part of this feature — see [Core Daily Rule](#core-daily-rule) below. It has one single authoritative, transaction-safe implementation on the backend; the frontend never computes eligibility itself.

---

## Where it lives

This is **not** a standalone module — it lives inside the existing Communication module:

| | Location |
|---|---|
| **UI** | **Communication → Vocabulary** tab (the default tab at `/communication`); word detail at `/communication/vocabulary/:id` |
| **API** | `/api/v1/communication/vocabulary/*` |
| **Backend code** | `backend/app/modules/communication/vocabulary/` |
| **Frontend code** | `frontend/src/app/features/communication/vocabulary/` |

It replaced the previous free-form "vocabulary notebook" (manual word/meaning entries, `VocabularyWord` / `vocabulary_words` table) that used to occupy the Communication → Vocabulary tab. That feature's model, routes, API, and UI were removed; its table was left in place untouched rather than dropped (this codebase has no destructive migration tooling by design).

---

## Data Import — syncing the JSON dataset into the database

The vocabulary dataset lives at `backend/app/modules/communication/vocabulary/seeds/practical-english-vocabulary.json` (15,000 items, `dataset_version: "1.0"`, source of truth for `id`/`term`/`level`/`type`/meanings/examples/etc.). **The app never reads this file at runtime** — it's imported once into the `vocabulary` table, and the API always serves from the database.

### Run the importer

```bash
cd backend
source .venv/bin/activate
python -m app.modules.communication.vocabulary.seeder
```

Output:

```
Imported: 15000
Inserted: 15000
Updated: 0
Skipped: 0
Errors: 0
```

- **Idempotent** — safe to re-run any time. A second run against the same file reports `Inserted: 0, Updated: 15000` (content refreshed, nothing duplicated).
- **Never renumbers** — `sequence_number` (parsed from the `vNNNNNN` id) is set once at insert and never changed on update, so the daily-sequencing order is stable even if you edit/re-import the dataset later.
- **Never touches user data** — importing does not create, modify, or delete anything in `user_vocabulary`, `vocabulary_sets`, bookmarks, or personal examples.
- **Validates before writing** — malformed records (bad id format, missing fields, invalid enum values, duplicate ids/terms) are reported in the summary and skipped, never silently dropped.

### Import a different or updated dataset

```bash
python -m app.modules.communication.vocabulary.seeder --file /path/to/other-dataset.json
```

Same rules apply: existing ids get their content updated, new ids get inserted, `sequence_number` for existing ids is untouched. To add a *second batch* of new words to the same collection later, give the new records ids that continue the sequence (e.g. `v015001`, `v015002`, ...) — the app makes no assumption that there are exactly 15,000 words (see [Dynamic dataset size](#dynamic-dataset-size)).

### When to re-run it

- After editing the JSON file (corrected definitions, added fields).
- After appending new records to the file (dataset growth).
- It is **not** run automatically on app startup or deploy — run it manually whenever the dataset changes.

---

## Core Daily Rule

The most important business rule in this feature:

1. A user gets **10 vocabulary items** at a time.
2. The next daily set becomes available only when **both**:
   - the previous daily set has been explicitly **Accepted**, and
   - the next **12:00 AM Asia/Kolkata** boundary has passed.
3. **Midnight alone never advances an unaccepted set.** If you don't click Accept, you keep seeing the same 10 words indefinitely — there is no cron job silently rotating them.

State is computed fresh every time you open the Vocabulary screen (`GET /communication/vocabulary/today`), from your stored progress pointer + your most recent set + the current IST date — never from a scheduled job.

### Change

Every card has a **Change** button (only while the set is still active/unaccepted). Clicking it replaces that one word with the next unused word in your personal sequence, and the replaced word is never reissued to you as new vocabulary again.

### Next Set

Once you've **Accepted** the current set, **Next Set** immediately allocates the next 10 words without waiting for midnight — useful if you want to keep going the same day.

### No repetition, guaranteed

Every word you're ever given as *new* vocabulary is recorded once in `user_vocabulary` under a `(user_id, vocabulary_id)` uniqueness constraint. Allocation is done inside a locked, transactional function (`allocate_next` in `sequencing.py`) so two simultaneous requests (e.g. two devices, or a double-click) can never hand out the same word twice.

---

## Bookmarks

Bookmark any word from its daily card or its detail page. Bookmarking/unbookmarking:
- is idempotent (bookmarking an already-bookmarked word is a no-op, not an error)
- **never** affects your daily sequence or `next_sequence_number`
- removing a bookmark **never** deletes your learning history for that word

---

## Personal Examples

On any word's detail page, add unlimited example sentences of your own (optionally with notes). These are stored separately from — and never overwrite — the dataset's original `example` field. Edit or delete your own examples any time.

---

## History

The **History** tab lists every set you've ever had, grouped by date, showing whether it was Accepted or still In Progress, and the actual words shown (including the effect of any Change you made — history reflects what you actually saw, not the original allocation).

---

## Progress Dashboard

Shows, all computed live from the database — **never hard-coded**:

| Tile | Meaning |
|------|---------|
| Vocabulary Learned | `X / total_available_vocabulary` — the denominator grows automatically as the dataset grows |
| Current Level | CEFR level of your most recently accepted word |
| Today's Progress | Items in your current set / set size, and whether it's accepted |
| Bookmarks | Total bookmarked words |
| Needs Revision | Words with `mastery_level <= 2` |
| Current Streak | Consecutive days with an accepted set, broken if a full day is missed |

---

## Search & Library

The **Library** tab searches the full dataset server-side (indexed `term`/`simple_meaning` match, plus level/type/topic filters) — the frontend never downloads the whole dataset to filter client-side. Results are paginated.

---

## Revision

Revision re-practices words you've **already learned** — it never allocates new vocabulary or advances your sequence. Sources:

| Source | Meaning |
|--------|---------|
| `today` | Today's already-learned words |
| `previous_day` | Yesterday's words |
| `date` | A specific date you pick |
| `all` | Every word you've ever learned |
| `bookmarked` | Your bookmarked words |
| `weak` | Words with low mastery (`mastery_level <= 2`) |
| `level` | A specific CEFR level among your learned words |
| `topic` | A specific topic tag among your learned words |

---

## Games

All 7 PRD-named game types run on the **same shared engine** — one multiple-choice builder and one matching-pairs builder, fed with your real learned-vocabulary pool — rather than 7 separate implementations:

| Game type | Mechanic |
|-----------|----------|
| Meaning Quiz | Pick the correct meaning for a word |
| Synonym Quiz | Pick a correct synonym |
| Antonym Quiz | Pick a correct antonym |
| Fill in the Blank | Pick the word that completes the (blanked) example sentence |
| Example Completion | Same as above, with the meaning shown as a hint |
| Word Matching | Match each word to its meaning |
| Meaning Matching | Match each word to its synonym (falls back to meaning if none) |

Pick a **source** the same way as Revision (Today / All Learned / Bookmarked / Needs Revision / a specific Level). Games:
- **never** consume new vocabulary or change `next_sequence_number`
- **do** update `times_reviewed`, `times_correct`/`times_incorrect`, and `mastery_level` (bounded 0–5, +1 on correct / -1 on incorrect) for each word answered
- are recorded as a `game_sessions` row (with per-question `game_questions` rows) once completed, visible under "Recent games"

---

## Dynamic dataset size

Nothing in this feature hard-codes "15,000". The available-word count, the progress denominator, and the "end of dataset" check are all computed at request time over the **daily-eligible** rows of `vocabulary` (`exclude_from_daily IS NOT TRUE`). Word Lab saves and Word of the Day rows are excluded; see [Word Lab and Word of the Day](#word-lab-and-word-of-the-day). You can grow the dataset to 20,000, 50,000, or 100,000+ items by re-running the importer with an updated/extended JSON file — no code changes needed.

---

## Word Lab and Word of the Day

Spec: `requirements/25sept-vocabulary-word-lab.md`. Setup: `setup/WORDNIK_SETUP.md`.

- **Word Lab tab** (`components/vocabulary-word-lab.component.ts`):
  - One search box plus tool chips: Dictionary, Synonyms, Explorer (reverse dictionary: describe an idea and get words), Rhymes, Game (Guess the word / Guess the meaning / Scramble), and **Saved** (the words added through Save as vocabulary, newest first).
  - The tab is locked, with a "Connect in Integrations" link, until the user saves a Wordnik key on `/integrations`. Keys are per user (BYOK) and Fernet-encrypted, and all vendor calls are server-side.
  - **Usage remaining %** comes from the last Wordnik rate-limit headers stored on the user's integration. It shows "Unknown" when no reading exists for the current clock hour.
- **Save as vocabulary** inserts a row into the same `vocabulary` table (`source="user_saved"`, id `x` + 15 hex chars). If the term already exists, case-insensitively, the existing id is returned instead. Saved rows open in the normal detail page and appear in Library search.
- **Word of the Day** is a header chip showing only the term (`shared/layout/word-of-the-day-chip.component.ts`), with a hover/tap popover. The popover sits flush under the chip and closes 300 ms after the pointer leaves, so small cursor slips don't close it. Clicking it opens `/communication/vocabulary/{id}`. It is hidden unless the current user has a connected key.
  - Lookup order:
    1. browser `localStorage` (`lifeos.wotd.<userId>.<IST date>`)
    2. `vocabulary.wotd_for_date = today`
    3. one Wordnik fetch, stored app-wide
  - If the term already exists, that row is reused (only `wotd_for_date` is set). Otherwise a `w<YYYYMMDD>` row with `source="api"` is inserted.
- **Columns** (additive): `source` (`dataset` | `api` | `user_saved`), `exclude_from_daily`, and `wotd_for_date` (unique index `ix_vocabulary_wotd_for_date`).
- **Sequencing rule:**
  - `get_next_unused` and `count_vocabulary` only consider rows with `exclude_from_daily IS NOT TRUE`, so saved and Word of the Day rows are never allocated as daily words and never inflate the progress denominator.
  - Non-dataset rows also take `sequence_number` from a reserved band starting at 1,000,000,000 (`RESERVED_SEQUENCE_START`), so future dataset imports (`v000001`–`v999999`) can never collide with them.

---

## API reference (authenticated; all under `/api/v1/communication/vocabulary`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/today` | Current daily state + set (computed on read) |
| POST | `/sets/{set_id}/accept` | Accept the active set |
| POST | `/sets/{set_id}/items/{position}/change` | Replace one word in the active set |
| POST | `/sets/next` | Manually allocate the next 10 (requires prior Accept) |
| GET | `/{vocabulary_id}` | Full word detail + your bookmark/mastery/example-count state |
| GET / POST / DELETE | `/bookmarks[, /{vocabulary_id}]` | List / add / remove bookmarks (paginated list) |
| GET / POST | `/{vocabulary_id}/examples` | List / add your personal examples |
| PATCH / DELETE | `/examples/{example_id}` | Edit / delete one of your personal examples |
| GET | `/history` | Paginated, date-grouped set history |
| GET | `/progress` | Progress dashboard numbers |
| GET | `/search` | `q`, `level`, `type`, `part_of_speech`, `topic`, `intent` filters, paginated |
| GET | `/revision` | `source`, `date`, `level`, `topic` params, paginated |
| GET | `/games/vocabulary` | Pool of learned words for a game `source` |
| POST | `/games/sessions` | Start a game session |
| POST | `/games/sessions/{id}/answers` | Submit one answer (updates mastery) |
| POST | `/games/sessions/{id}/complete` | Finalize a session's score |
| GET | `/games/history` | Paginated list of completed sessions |
| GET | `/word-lab/status` | `{connected, usage_remaining_pct}`. No vendor call. |
| GET | `/word-lab/lookup` | `q`, `mode=dictionary\|synonyms\|explorer\|rhymes`. Proxied to Wordnik. |
| GET | `/word-lab/game` | `type=guess_word\|guess_meaning\|scramble`. A stateless practice round. |
| GET | `/word-lab/saved` | Word Lab saves (`source="user_saved"`), newest first, paginated |
| POST | `/word-lab/save` | Save a looked-up word into `vocabulary` (returns the existing id if the term is already there) |
| GET | `/word-of-the-day` | `{connected, date, vocabulary}`. DB first; Wordnik at most once per IST day. |

Every endpoint derives the user from the JWT (`Depends(get_current_user)`) and scopes every query by `user_id` at the repository layer — a client can never read or modify another user's progress, bookmarks, examples, or game history.

---

## Architecture

```
Master vocabulary (JSON → import → `vocabulary` table)
        │
        ▼
User progress pointer (`user_vocabulary_progress.next_sequence_number`)
        │  locked + advanced only by allocate_next()
        ▼
Daily sets (`vocabulary_sets` + `vocabulary_set_items`)
        │
        ▼
Learning history / no-repeat record (`user_vocabulary`)
        │
   ┌────┼────────┬───────────┬────────────┐
   ▼    ▼        ▼           ▼            ▼
Bookmarks  Examples   Revision      Games (game_sessions/game_questions)
```

Master content (`vocabulary`, `vocabulary_collections`) is kept separate from per-user learning state (`user_vocabulary_progress`, `vocabulary_sets`, `user_vocabulary`) and from the learning experience built on top (bookmarks, examples, revision, games) — so a future second dataset/collection, or a future spaced-repetition algorithm, doesn't require redesigning the core tables. `user_vocabulary` already carries `next_review_at`/`review_interval`/`repetition_count`/`ease_factor` columns reserved for a future SR algorithm, unused today.

### Key files

**Backend** (`backend/app/modules/communication/vocabulary/`):
| File | Purpose |
|------|---------|
| `models.py` | 9 tables: collections, vocabulary, progress, sets, set items, user_vocabulary, bookmarks, examples, game sessions/questions |
| `sequencing.py` | The one authoritative `allocate_next()` + `resolve_daily_state()` (daily state machine) |
| `mastery.py` | Small, replaceable `next_mastery_level()` |
| `repository.py` / `service.py` / `api.py` / `schemas.py` | Standard data/business/HTTP/validation layering |
| `seeder.py` | The idempotent JSON importer (see [Data Import](#data-import--syncing-the-json-dataset-into-the-database)) |
| `seeds/practical-english-vocabulary.json` | The source dataset |

**Frontend** (`frontend/src/app/features/communication/vocabulary/`):
| File | Purpose |
|------|---------|
| `vocabulary-hub.component.ts` | Tabbed shell: Today's Words / Library / History / Progress / Games — embedded in the Communication hub's **Vocabulary** tab |
| `vocabulary-daily.component.ts` | Daily set screen (Accept/Change/Next Set) |
| `vocabulary-detail.component.ts` | Full word detail + bookmark + personal examples (route `/communication/vocabulary/:id`) |
| `components/vocabulary-library.component.ts` | Search + filters |
| `components/vocabulary-history.component.ts` | Grouped history list |
| `components/vocabulary-progress.component.ts` | Dashboard tiles |
| `components/vocabulary-games.component.ts` | Game setup/play/results |
| `games/question-builder.ts` | Pure functions building MC questions / matching pairs from a vocabulary pool |
| `services/vocabulary.service.ts` | Single HTTP client — the frontend's only source of backend state |

Shared `app/core/timezone.py::ist_today()`/`ist_now()` provides the fixed Asia/Kolkata boundary used by the daily state machine.

---

## Security & data integrity notes

- Every endpoint requires auth; every query is scoped to the authenticated `user_id` at the repository layer — no client-supplied `user_id` is ever trusted.
- Sequence allocation is transaction-safe: a `SELECT ... FOR UPDATE` lock on Postgres (a real row lock) plus a `UniqueConstraint(user_id, vocabulary_id)` backstop (works on SQLite too, where the lock clause is accepted but not enforced by the dialect).
- No destructive migrations exist for this feature (or anywhere in this codebase) — schema changes are additive `create_all` + optional idempotent `ALTER TABLE ADD COLUMN`.
- This module is unrelated to `communication`'s `VocabularyWord` personal-notebook feature (different tables, different routes) — the two coexist deliberately.

---

## Testing

```bash
cd backend
source .venv/bin/activate
python -m pytest app/tests/test_vocabulary_sequencing.py app/tests/test_vocabulary_pbt.py \
  app/tests/test_vocabulary_import.py app/tests/test_vocabulary_stage2.py \
  app/tests/test_vocabulary_games.py -v
```

45 tests: example-based coverage of every PRD rule (new-user order, accept/next-day, unaccepted-persists-across-midnight, change never repeats, next-set gating, user isolation, reload consistency, concurrent-change safety, end-of-dataset, bookmarks, personal examples, revision, history, progress, search, games), plus 7 Hypothesis property-based tests (import validation/idempotence, allocation never-repeats + pointer invariant, mastery bounds).

Frontend:

```bash
cd frontend
npm run test:ci
```
