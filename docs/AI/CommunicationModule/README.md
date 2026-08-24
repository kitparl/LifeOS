# Communication Module — AI Writing Feedback

How to connect Sarvam, run AI Feedback on your writing, and how the feature is built in LifeOS.

This is **Phase 1 (MVP)**: evaluate writing with a stable rubric, store results, avoid duplicate billed calls, and keep your own API key (BYOK). Writing Coach, progress dashboards, and personalized practice are deferred.

---

## What it does

1. You paste a **Sarvam API key** under Integrations (encrypted at rest).
2. You write in **Communication → Writing** (markdown editor).
3. On a saved writing’s detail page, click **AI Feedback**.
4. LifeOS returns:
   - Overall score (computed by the app from dimension weights — not trusted from the LLM alone)
   - 13 rubric dimensions (0–100)
   - Strengths, issues, suggestions
   - Deterministic metrics (word count, sentence count, etc.)
5. If you click again on **unchanged** content + same model/rubric versions, the saved evaluation is returned — **no second Sarvam call** (saves your quota/money).

---

## How to connect Sarvam

1. Create an API key at [dashboard.sarvam.ai](https://dashboard.sarvam.ai/).
2. In LifeOS open **Integrations** (`/integrations`).
3. Find **Sarvam AI**.
4. Paste the **API subscription key** into the secret field.
5. Enable Sarvam, click **Save**, then **Test connection**.
6. After save, only a masked value (e.g. `****9999`) is shown — the raw key is never redisplayed.

Usage is billed to **your** Sarvam account. LifeOS does not pay for your AI calls.

Official docs: [Sarvam AI Welcome](https://docs.sarvam.ai/api/getting-started/welcome) · [Chat Completions / sarvam-105b](https://docs.sarvam.ai/api/getting-started/models/sarvam-105b)

---

## How to get feedback on writing

1. Go to **Communication** → Writing.
2. Create or open a piece and **save** it (feedback needs a writing id).
3. On the writing **detail** page, use the **AI Feedback** panel.
4. If you see “Connect your Sarvam API key…”, follow the link to Integrations.

Empty writing cannot be evaluated until you add content.

---

## Model selection (per use case)

LifeOS can bind a **use case** (e.g. `communication.writing_feedback`) to a provider/model.

| API | Purpose |
|-----|---------|
| `GET /api/v1/ai/use-cases` | List use cases, options, current selection |
| `PUT /api/v1/ai/use-cases/{use_case}/model` | Set `{ "provider", "model" }` |
| `GET /api/v1/ai/use-cases/{use_case}/history` | Past selections with `effective_from` / `effective_to` |

**v1 catalog:** only `communication.writing_feedback` → `sarvam` / `sarvam-105b`.

Every evaluation row also stamps `provider` / `model` / `prompt_version` / `rubric_version` so later model changes do not silently rewrite history.

---

## Architecture (short)

```text
Writing editor (Angular)
        │
        ▼
POST /communication/writing/{id}/ai-feedback
        │
        ├─ resolve use-case model (ai module)
        ├─ decrypt Sarvam key (integrations / Fernet)
        ├─ evaluation_key = hash(content + versions + provider + model)
        ├─ if row exists → return cached evaluation
        └─ else → SarvamWritingProvider (httpx)
                      │
                      ▼
              api.sarvam.ai /v1/chat/completions
              model=sarvam-105b
              reasoning_effort=None (cost control)
```

**Adapter pattern:** domain code talks to `AIWritingProvider`; only `evaluate_writing()` is implemented in Phase 1. Sarvam-specific HTTP stays in `backend/app/modules/communication/ai/provider.py`.

### Key code locations

| Area | Path |
|------|------|
| Use-case catalog / selection | `backend/app/modules/ai/use_cases.py`, `models.py`, `service.py` |
| Sarvam BYOK | `backend/app/modules/integrations/sarvam_config.py`, Integrations UI |
| Rubric / metrics / adapter | `backend/app/modules/communication/ai/` |
| Evaluate API | `POST/GET .../communication/writing/{id}/ai-feedback` |
| Feedback panel | `frontend/.../writing-feedback-panel.component.ts` |

---

## Cost controls (always on for this feature)

- BYOK — your key, your bill
- Idempotency before any network call
- `reasoning_effort=None` (Sarvam defaults reasoning on; that would waste tokens)
- Tight `max_tokens`, low temperature, `n=1`, no streaming
- Input content capped (~12k characters); UI notes truncation if applied
- No auto-evaluate on save / no background polling

---

## Adding another LLM later

1. Add the provider to Integrations the same way as Sarvam (encrypt key in `config_json`).
2. Implement another class conforming to `AIWritingProvider`.
3. Add a catalog option under the use case in `use_cases.py`.
4. Resolve credentials in `CommunicationService.evaluate_writing` when `provider` matches.

No change to the writing editor business flow is required beyond wiring the new adapter.

---

## Related requirements

Full product vision and later phases: `requirements/24Aug.md`  
AI-DLC condensed requirements: `aidlc-docs/inception/requirements/requirements-24aug-communication-ai.md`
