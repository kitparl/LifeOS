# LifeOS — Claude Code project instructions

## AI-DLC

When the user invokes AI-DLC (e.g. "Using AI-DLC, ..."), read and follow
`.aidlc/aidlc-rules/aws-aidlc-rules/core-workflow.md` to start the workflow.

Rule details live under `.aidlc/aidlc-rules/aws-aidlc-rule-details/`
(also reachable via the `.aidlc-rule-details` symlink).

## Project layout

- `backend/` — FastAPI app
- `frontend/` — Angular 19 app
- `aidlc-docs/` — AI-DLC artifacts (gitignored; generated during workflows)
- `scripts/setup-aidlc.sh` — install/update AI-DLC rules for Cursor **and** Claude Code

## UI

Do not redesign the existing UI unless asked. Prefer the project's current
design system (Ubuntu-style theme where present). See `.claude/rules/ui-style.md`.
