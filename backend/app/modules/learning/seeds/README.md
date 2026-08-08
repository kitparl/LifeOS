# Learning Track Seeds

Drop a JSON file into this directory to add a new curriculum track. **No code changes required.**

## How to add a track

1. Copy `ai-systems-engineering.json` as a starting point, or write a new file named `{slug}.json`.
2. `slug` must match `^[a-z0-9][a-z0-9-]{0,63}$` and must equal the filename (without `.json`).
3. Files starting with `_` are reserved (schema, docs) and cannot be seeded.
4. Validate shape against [`_schema.json`](_schema.json).
5. Seed via API or CLI:

```bash
# API (authenticated)
curl -X POST /api/v1/learning/tracks/seed \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug":"ai-systems-engineering"}'

# CLI
cd backend && python -m app.modules.learning.seeder ai-systems-engineering --email you@example.com
```

## Resource curation rules

Every concept must carry at least one resource (a test enforces this). When adding them:

- One canonical source per idea — prefer primary docs over blog restatements.
- Videos only where a video teaches better (intuition, build-from-scratch, project walk-throughs).
- Papers only where the paper is the clearest and shortest source.
- No filler: no listicles, no course landing pages, no `awesome-*` dumps.
- `priority: primary` = read it; `supporting` = skim if the primary one didn't land.
- Put the required depth (and where to stop) in the concept `summary`; the seeder refreshes it.
- Set `last_verified_at` when you add or re-check a URL.

Resources on a **phase** apply to all its concepts: they render under the phase on the track
view and as `inherited_resources` on every concept in that phase.

## Seeder contract

- Idempotent: re-running updates titles/URLs/order but **never** overwrites user progress
  (`confidence`, `can_explain`, `failure_modes_known`, `tradeoffs_known`, `artifact_url`,
  `is_consumed`, `notes`, `completed_at`).
- Keys: track slug per user → phase slug per track → concept slug per phase → resource URL per concept.
- Progress on phases rolls up from `can_explain` ratio after concept patches.
