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

# Project Rules

## 0. Role & Mindset
- Approach every task as a Senior Engineer / Architect would — think about maintainability, scalability, and edge cases before writing code, not after.
- Before implementing, briefly reason through: "What would a senior engineer reviewing this PR flag?" and address it upfront.
- Evaluate trade-offs (performance vs. readability, flexibility vs. simplicity) explicitly when a decision isn't obvious, instead of picking the first working approach.
- Think about how this code will be maintained, extended, and debugged by someone else in 6 months.
- Flag risky decisions (breaking changes, security implications, tight coupling) instead of silently proceeding.
- When multiple valid approaches exist, briefly state which was chosen and why — don't just pick silently.

## 1. Code Simplicity
- Do not over-engineer. Solve the problem in front of you, not the one you imagine you might have later.
- Avoid unnecessary abstraction (extra interfaces, factories, config layers) for logic used in only one place and unlikely to change.
- Prefer the simplest solution that is correct and readable over the "clever" one.
- No speculative generalization — don't add flexibility/config options for hypothetical future use cases (YAGNI).

## 2. Patterns & Architecture
- Follow the existing pattern already used in the codebase for similar use cases.
- If it's a genuinely new kind of problem with no existing precedent, pick the most widely accepted, idiomatic pattern for that language/framework — not an unconventional one.
- Don't introduce a new pattern, library, or architectural style when an existing one already solves the problem.
- Keep layering consistent (e.g. controller → service → repository) — don't skip layers or mix responsibilities.

## 3. DRY / Reuse
- Before writing new logic, search the codebase for an existing function, utility, service, or module that already does it (or close to it).
- If logic is used — or will plausibly be used — by more than one module/service/entity, extract it into a shared/common location (e.g. `common/`, `shared/`, `libs/`) instead of duplicating it.
- Don't copy-paste code with small tweaks — parameterize and reuse instead.
- Consolidate duplicate types/interfaces/DTOs rather than redefining the same shape in multiple places.
- Reuse existing constants/enums instead of hardcoding values.

## 4. Coding Principles
- Follow SOLID where it genuinely helps (especially single-responsibility) — don't apply patterns dogmatically at the cost of simplicity.
- Keep functions small and focused; one function should do one thing.
- Meaningful naming over comments explaining unclear names.
- Consistent error handling — don't mix silent failures, thrown exceptions, and returned error objects in the same codebase.
- Type everything explicitly (no implicit `any`, no loose typing) where the language supports it.

## 5. Before Writing Code
- Check for existing utilities, hooks, services, or constants before creating new ones.
- Check for existing types/interfaces before redefining.
- If unsure whether something already exists, search/grep first rather than assuming.
- Understand the existing data flow/module boundaries before adding new code.

## 6. Scope Discipline
- Don't refactor unrelated code while implementing a feature/fix — flag it separately instead.
- Don't add extra features, validations, or configs that weren't asked for "just in case."
- Keep changes minimal and scoped to the task.
- Don't rename/move existing files or symbols unless required for the task.

## 7. Testing & Validation
- Don't skip validation on inputs that cross a trust boundary (API inputs, webhook payloads, etc.).
- Add/update tests for new logic where the codebase already has a testing pattern in place.
- Don't leave dead code, commented-out blocks, or unused imports behind.

## 8. Communication
- If a requirement is ambiguous, ask rather than assume and build the wrong thing.
- If an existing pattern is clearly bad/outdated, flag it and suggest an alternative — don't silently deviate from it.
