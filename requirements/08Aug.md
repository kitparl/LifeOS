# AI Systems Engineering Learning Track — Plan & Implementation Spec

**Date:** 08 Aug 2026
**Owner:** Pranshu Bisht
**Goal:** Backend Engineer → AI/GenAI Backend Engineer → Agentic AI Engineer → AI Systems / Platform Engineer
**Commitment:** ~1–1.5 hrs weekdays + 3–4 hrs weekend ≈ **10–12 hrs/week**
**Duration:** **24 weeks (6 months)** — 08 Aug 2026 → ~23 Jan 2027

This document has three parts:

1. **The plan** — gap analysis, 24-week schedule, curated resources per phase
2. **The implementation spec** — how to model this inside LifeOS so other tracks can be added later
3. **The kickoff prompts** — copy-paste prompts to start building and to start each study session

---

# PART 1 — THE PLAN

## 1.1 Gap analysis

### Already have (transferable — do not re-learn)

Roughly 40% of production AI engineering is distributed-systems work already done in payments:

| Existing skill | Maps directly to |
|---|---|
| Multi-gateway payment routing + fallback | LLM model routing + provider fallback |
| Retries, backoff, timeouts, circuit breakers | LLM call reliability |
| Idempotency keys | Agent step re-execution safety |
| Wallet/ledger accounting | Token accounting + cost attribution |
| Kafka event-driven workflows | Async agent run orchestration |
| Saga / compensating transactions | Human-in-the-loop approval + rollback |
| Distributed tracing, metrics | LLM tracing (spans + token/cost attributes) |
| API contracts, schema validation | Tool schemas, structured outputs |
| DB index tuning | Vector index tuning (HNSW / IVF) |
| Rate limiting, quota management | Provider quota + tenant throttling |
| K8s / Docker / AWS | Model serving deployment |

### Genuinely need to learn

The hardest item is a **mental model shift, not a technology**: moving from deterministic systems to statistical ones. The instinct to "assert exact output" stops working. That single shift is why evaluation is the largest gap.

Beyond that: tokens/context as a capacity-planning resource; embedding and similarity intuition; retrieval quality engineering; context engineering as a discipline; agent loop control and autonomy budgeting; prompt injection as a new vulnerability class where data becomes code; GPU inference economics.

### Explicitly skip

- Writing a transformer from scratch; deriving attention math
- Classical ML — sklearn, feature engineering, XGBoost, Kaggle (**different job**)
- Memorising LangChain / LangGraph API surface
- Framework-of-the-month chasing
- Fine-tuning before month 5 (most production systems never need it)
- Certificates — zero signal for this role

### Gaps ranked by importance

1. **Evaluation** — separates demo from system; most candidates lack it entirely
2. Retrieval quality engineering
3. Context engineering
4. Agent loop architecture
5. Probabilistic failure taxonomy
6. LLM internals (only enough to reason about cost/latency)
7. Python fluency
8. AI-specific security
9. Inference infrastructure
10. Fine-tuning

### Proving competence without certificates

- Repos whose README **leads with** a latency / cost / quality table and an ablation study
- Written teardowns of own design decisions and failures
- **Internal adoption at current job** (strongest available signal)
- Reproducible benchmarks others can run

---

## 1.2 The 24-week schedule

| Wk | Dates | Phase | Focus | Deliverable |
|---|---|---|---|---|
| 1 | Aug 08–14 | P1 | Decode loop, tokenization, context window, sampling, embeddings intro | Instrument `OpenAiProvider` — log tokens in/out, latency, cost |
| 2 | Aug 15–21 | P2 | LLM APIs, message roles, structured outputs, function calling, streaming | Replace regex JSON parsing in `parse_and_create_task` with structured output |
| 3 | Aug 22–28 | P2 | Retries, timeouts, fallback, model routing, caching, rate limits, concurrency | Reliability layer with circuit breaker |
| 4 | Aug 29–Sep 04 | P2 | Prompt injection, PII, secrets | **Project 1: LLM Gateway & Router** |
| 5 | Sep 05–11 | P3 | Embedding spaces, cosine similarity, HNSW vs IVF vs flat, pgvector | Migrate `embedding_json` → pgvector |
| 6 | Sep 12–18 | P3 | Chunking, ingestion, metadata, BM25, hybrid search, RRF | Replace `vector_score * 10 + keyword_score` with RRF |
| 7 | Sep 19–25 | P3 | Reranking, query rewriting, multi-query, parent-child, contextual retrieval | Add reranker; incremental indexing via content hash |
| 8 | Sep 26–Oct 02 | P3+P6 | Retrieval metrics: recall@k, MRR, nDCG, faithfulness | **Project 2: Ops RAG + eval harness**, published before/after |
| 9 | Oct 03–09 | P4 | Workflows vs agents, ReAct, reason/act loop, autonomy degrees | Hand-rolled agent loop, no framework |
| 10 | Oct 10–16 | P4 | Tool design, schemas, selection, error handling, idempotency | Tool-using agent |
| 11 | Oct 17–23 | P4 | State, short/long/episodic memory, persistence, checkpoints, recovery | Stateful agent surviving process restart |
| 12 | Oct 24–30 | P4 | Multi-agent, supervisor/worker, hierarchical, HITL, approval gates | Multi-agent + approval workflow |
| 13 | Oct 31–Nov 06 | P5 | LangGraph — map every abstraction to own implementation | Port week 9–12 agent; document what the framework bought |
| 14 | Nov 07–13 | P5 | MCP: problem, architecture, transport, security, when direct APIs win | One MCP server, one MCP client |
| 15 | Nov 14–20 | P6 | Golden datasets, deterministic tests, LLM-as-judge, judge bias | Golden dataset for Project 2 |
| 16 | Nov 21–27 | P6 | Trajectory eval, tool-call correctness, regression testing, red teaming | Eval gate in CI |
| 17 | Nov 28–Dec 04 | P7 | Tracing, structured logging, token/cost metrics, SLO design | OpenTelemetry across all projects |
| 18 | Dec 05–11 | P7 | Guardrails, PII redaction, audit logs, injection defence | Guardrail layer + audit trail |
| 19 | Dec 12–18 | P10 | Flagship: requirements → architecture → design decisions | **Project 3** design doc |
| 20 | Dec 19–25 | P10 | Flagship build | Working agent end-to-end |
| 21 | Dec 26–Jan 01 | P8 | Batching, continuous batching, KV cache, quantization, throughput vs latency | Benchmark local model |
| 22 | Jan 02–08 | P8 | vLLM, Ollama, GPU economics, autoscaling, K8s + AWS deploy | Flagship deployed |
| 23 | Jan 09–15 | P9 | RAG vs fine-tuning decision, LoRA/QLoRA/PEFT — **decision-level only** | Written decision framework |
| 24 | Jan 16–22 | P10 | AI system design drills + interview prep | Mock system designs |

### Daily rhythm

- **~30 min** — concept (one at a time, never two)
- **~45 min** — build
- **~15 min** — write it down in own words

The writing is not optional. It is the retention mechanism and the interview rehearsal.

### Depth gate — do not advance until all four are true

1. Can explain the concept to another engineer **without notes**
2. Can name at least two **failure modes**
3. Can state the **trade-off** against the alternative
4. Have shipped a **working artifact** (`artifact_url` recorded)

---

## 1.3 Curated resources per phase

> **Link policy:** verified 08 Aug 2026. YouTube playlist IDs and course URLs change. Resources are stored as **seed data, not hardcoded** (see Part 2) precisely so they can be corrected without a code change. Run the link-check script monthly.

### Channel / source index

| Source | URL | Fit for this track |
|---|---|---|
| Krish Naik | https://www.youtube.com/@krishnaik06 | **High** — agentic AI + GenAI, project-heavy |
| Krish Naik — Agentic AI roadmap repo | https://github.com/krishnaik06/Roadmap-To-Learn-Agentic-AI | **High** — the most durable single index |
| freeCodeCamp | https://www.youtube.com/@freecodecamp | **High** — long-form production courses |
| DeepLearning.AI courses | https://www.deeplearning.ai/courses/ | **High** — best conceptual grounding |
| DeepLearning.AI short courses | https://www.deeplearning.ai/short-courses/ | **High** |
| DeepLearning.AI — The Batch | https://www.deeplearning.ai/the-batch/ | Medium — weekly signal |
| Sheryians AI School | https://www.youtube.com/@sheryiansai | **Low** — see note below |

**Note on Sheryians AI School:** the channel is Hindi-language, ~103K subs, oriented toward Python / data-science beginners and students; their GenAI content is a bonus track inside a paid full-stack cohort (https://bootcamp.sheryians.com/). It is a good channel for its audience, but it is **below the level of a backend engineer with 3+ years of production experience**. Included in the seed as `priority: optional` for completeness — do not budget hours against it. If a specific Sheryians video is wanted later, add it to the seed JSON; nothing in the schema prevents it.

---

### PHASE 1 — LLM Foundations (Week 1)

| Type | Resource | URL |
|---|---|---|
| Video | Karpathy — Intro to Large Language Models (1 hr) | https://www.youtube.com/watch?v=zjkBMFhNj_g |
| Video | Karpathy — Let's build the GPT Tokenizer | https://www.youtube.com/watch?v=zduSFxRajkE |
| Video | 3Blue1Brown — But what is a GPT? | https://www.youtube.com/watch?v=wjZofJX0v4M |
| Video | 3Blue1Brown — Attention in transformers | https://www.youtube.com/watch?v=eMlx5fFNoYc |
| Article | Jay Alammar — The Illustrated Transformer | https://jalammar.github.io/illustrated-transformer/ |
| Playlist | Krish Naik — Generative AI Tutorials | https://www.youtube.com/playlist?list=PLA1lVIthbM1D5I6r5uY2K89X1KD2w5LNh |
| Docs | OpenAI — Text generation & prompting | https://platform.openai.com/docs/guides/text |

**Skip:** the maths-heavy back half of any transformer video. Watch for *intuition about cost and latency*, not for the derivation.

---

### PHASE 2 — LLM Application Engineering (Weeks 2–4)

| Type | Resource | URL |
|---|---|---|
| Docs | OpenAI — Structured Outputs | https://platform.openai.com/docs/guides/structured-outputs |
| Docs | OpenAI — Function calling | https://platform.openai.com/docs/guides/function-calling |
| Docs | Anthropic — Tool use | https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview |
| Cookbook | OpenAI Cookbook | https://cookbook.openai.com/ |
| Security | OWASP Top 10 for LLM Applications | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |
| Course | DeepLearning.AI — short courses index | https://www.deeplearning.ai/short-courses/ |
| Blog | Chip Huyen — engineering blog | https://huyenchip.com/blog/ |

---

### PHASE 3 — Embeddings & RAG (Weeks 5–8)

| Type | Resource | URL |
|---|---|---|
| Course | DeepLearning.AI — Retrieval Augmented Generation (covers BM25, RRF, RAGAS, cost vs quality, tracing) | https://www.deeplearning.ai/courses/retrieval-augmented-generation |
| Video | freeCodeCamp — Production RAG with LangChain & Vector Databases (8 hr) | https://www.youtube.com/watch?v=mHxLXzYjQRE |
| Article | freeCodeCamp — companion write-up for the above | https://www.freecodecamp.org/news/production-rag-with-langchain-vector-databases/ |
| Video | freeCodeCamp — RAG Fundamentals and Advanced Techniques | https://www.youtube.com/watch?v=ea2W8IogX80 |
| Article | Anthropic — Contextual Retrieval | https://www.anthropic.com/news/contextual-retrieval |
| Playlist | Krish Naik — MultiModal RAG | https://www.youtube.com/playlist?list=PLQxDHpeGU14D6dm0rmAXhdLeLYlX2zk7p |
| Docs | pgvector | https://github.com/pgvector/pgvector |

**The freeCodeCamp 8-hour course is the single highest-value item in Phase 3** — it explicitly covers scaling, real cost of vector search, pgvector/Supabase, and LangSmith observability, which is exactly the production angle needed. Watch it across weeks 6–7, not in one sitting.

---

### PHASE 4 — Agentic AI (Weeks 9–12)

| Type | Resource | URL |
|---|---|---|
| Article | Anthropic — Building Effective Agents (**read first, twice**) | https://www.anthropic.com/engineering/building-effective-agents |
| Article | Lilian Weng — LLM Powered Autonomous Agents | https://lilianweng.github.io/posts/2023-06-23-agent/ |
| Course | DeepLearning.AI — Agentic AI (builds patterns from first principles *before* frameworks) | https://www.deeplearning.ai/courses/agentic-ai |
| Course | DeepLearning.AI — Agent Memory: Building Memory-Aware Agents | https://www.deeplearning.ai/courses/agent-memory-building-memory-aware-agents |
| Playlist | Krish Naik — Agentic AI Tutorials | https://www.youtube.com/playlist?list=PLZoTAELRMXVPFd7JdvB-rnTb_5V26NYNO |
| Playlist | Krish Naik — Agentic AI with different frameworks | https://www.youtube.com/playlist?list=PLZoTAELRMXVMBr14UQ30AFlnlQ7eL5wjl |
| Repo | Krish Naik — Roadmap To Learn Agentic AI | https://github.com/krishnaik06/Roadmap-To-Learn-Agentic-AI |

---

### PHASE 5 — Agent Frameworks + MCP (Weeks 13–14)

| Type | Resource | URL |
|---|---|---|
| Docs | LangGraph | https://langchain-ai.github.io/langgraph/ |
| Docs | Model Context Protocol — spec & concepts | https://modelcontextprotocol.io/ |
| Docs | MCP — Architecture | https://modelcontextprotocol.io/docs/concepts/architecture |
| Docs | CrewAI (skim only) | https://docs.crewai.com/ |

**Highest churn section in this document.** Concepts (state machines, checkpointing, supervisor/worker) are durable. Every API on this list is not.

---

### PHASE 6 — Evaluation (Weeks 15–16)

| Type | Resource | URL |
|---|---|---|
| Course | DeepLearning.AI — Building and Evaluating Data Agents (LLM-as-judge, goal/plan/action alignment, inline runtime evals) | https://www.deeplearning.ai/short-courses/building-and-evaluating-data-agents/ |
| Docs | RAGAS | https://docs.ragas.io/ |
| Docs | promptfoo | https://www.promptfoo.dev/docs/intro/ |
| Docs | DeepEval | https://docs.confident-ai.com/ |
| Docs | LangSmith — evaluation | https://docs.smith.langchain.com/evaluation |

---

### PHASE 7 — Production AI / LLMOps (Weeks 17–18)

| Type | Resource | URL |
|---|---|---|
| Docs | OpenTelemetry — GenAI semantic conventions | https://opentelemetry.io/docs/specs/semconv/gen-ai/ |
| Docs | Langfuse (open-source LLM observability) | https://langfuse.com/docs |
| Article | OWASP LLM Top 10 (revisit with production eyes) | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |

Most of this phase maps onto existing knowledge. Budget the saved time toward Phase 6.

---

### PHASE 8 — Model Serving & Infrastructure (Weeks 21–22)

| Type | Resource | URL |
|---|---|---|
| Docs | vLLM | https://docs.vllm.ai/ |
| Docs | vLLM — paged attention / KV cache design | https://docs.vllm.ai/en/latest/design/kernel/paged_attention.html |
| Docs | Ollama | https://ollama.com/ |
| Docs | Hugging Face — Text Generation Inference | https://huggingface.co/docs/text-generation-inference |

---

### PHASE 9 — Fine-Tuning (Week 23, decision-level only)

| Type | Resource | URL |
|---|---|---|
| Docs | Hugging Face PEFT | https://huggingface.co/docs/peft |
| Docs | Hugging Face — LoRA conceptual guide | https://huggingface.co/docs/peft/conceptual_guides/lora |
| Docs | OpenAI — fine-tuning guide | https://platform.openai.com/docs/guides/fine-tuning |

**Deliverable is a written decision framework, not a trained model.**

---

## 1.4 The three portfolio projects

### Project 1 — LLM Gateway & Router (Week 4)
Multi-provider routing with fallback, semantic caching, per-tenant rate limiting and quota, streaming, structured output enforcement, token ledger with cost attribution, full tracing. **This is the payments background expressed in AI terms** — it reads as senior immediately.

### Project 2 — Ops Knowledge RAG + eval harness (Week 8)
Over payment runbooks, gateway docs, error-code catalogs. The differentiator is not the RAG — it is publishing recall@k, MRR, faithfulness, p95 latency and cost/query, with a documented **ablation** showing what each technique bought.

### Project 3 — Payment Investigation Agent (Weeks 19–22, flagship)
Given a transaction or refund ID, investigates across ledger, gateway responses and Kafka event stream; retrieves relevant runbooks; forms a root-cause hypothesis; proposes remediation; routes to a human for approval; executes idempotently.

Consumes Projects 1 and 2 as components. Covers Kafka + RAG + tools + HITL + eval + observability + K8s + AWS in one artifact, in a domain that can be defended under questioning better than any interviewer can attack it.

---

## 1.5 Durable vs disposable

**Durable (will still matter in 5 years):** information retrieval and ranking, evaluation methodology, context engineering, distributed systems applied to nondeterminism, cost/latency modelling, security with untrusted input, tool and API design, architectural judgment.

**Disposable (expect to re-learn):** every framework API surface, specific model names/prices/context limits, provider SDK details, "prompt tricks", vector DB vendor specifics, and — flagged explicitly — the **MCP wire spec**. The problem MCP solves is durable; the current spec is not.

---

# PART 2 — IMPLEMENTATION SPEC (LifeOS)

## 2.1 Decision

**Extend the existing `learning` module. Do not create a new one.**

Rationale: LifeOS has no plugin system. A "module" is a convention (`models.py` → `repository.py` → `service.py` → `schemas.py` → `api.py`) manually wired into six places. A new module pays that cost again for zero domain benefit — `LearningItem` already has `item_type="study_plan"` and `interview_prep`.

**Scope confirmed:** extend `learning` with curriculum + session tracking, **and** use `backend/app/modules/ai/` as the hands-on upgrade target for Phases 2, 3, 6, 7.

## 2.2 Why the `ai` module is the lab

`backend/app/modules/ai/service.py` is a hand-rolled RAG pipeline whose every shortcut maps to a roadmap concept:

| Current shortcut | Location | Teaches |
|---|---|---|
| Loads **all** user embeddings into Python, brute-force cosine in a loop | `service.py::_retrieve` | ANN indexes; when O(n) scan is actually correct |
| Embeddings stored as JSON text | `models.py::ContentEmbedding.embedding_json` | pgvector, vector storage trade-offs |
| `clear_user_index()` then full re-embed on every index | `service.py::index` | Incremental indexing, content hashing, cost control |
| No chunking; truncates at `doc.content[:8000]` | `service.py::index` | Chunking strategy |
| `score = vector_score * 10 + keyword_score` | `service.py::_retrieve` | Score normalisation; why RRF exists |
| No reranking, no query rewriting | `service.py::_retrieve` | Advanced RAG |
| `except Exception: embedding_json = None` | `service.py::index` | Silent quality degradation; observability |
| Prompt asks for JSON, then `re.search(r"\{.*\}")` | `service.py::parse_and_create_task` | Structured outputs / function calling |
| User content interpolated into system prompt undelimited | `service.py::chat` | **Prompt injection — real vulnerability in this app** |
| `temperature=0.4` hardcoded, no token accounting, no streaming | `provider.py` | Sampling, cost tracking, streaming |

Each weekly deliverable in §1.2 targets one row of this table. Fixing them produces measurable before/after numbers — which is the portfolio evidence.

## 2.3 Data model (extensible — new tracks are data, not code)

Design goal: **adding a future track ("System Design", "Rust", "Kubernetes") must require zero schema changes and zero code changes — only a new seed JSON file.**

```
LearningTrack            (NEW)  "AI Systems Engineering"  slug: ai-systems-engineering
  └── LearningItem       (EXISTING, + nullable track_id)  one row per PHASE, item_type="study_plan"
        └── LearningConcept   (NEW)  atomic teachable unit, ordered, week-tagged
              ├── LearningResource (NEW)  youtube / article / docs / course / repo
              └── StudySession     (NEW)  logged time + confidence + artifact
```

### New tables

```python
# backend/app/modules/learning/models.py

TRACK_STATUSES  = ("planned", "active", "completed", "paused")
RESOURCE_TYPES  = ("video", "playlist", "article", "docs", "course", "paper", "repo", "book")
RESOURCE_PRIORITY = ("primary", "supporting", "optional")


class LearningTrack(Base):
    __tablename__ = "learning_tracks"

    id: Mapped[str]                      # uuid4
    user_id: Mapped[str]                 # FK users.id, indexed
    slug: Mapped[str]                    # unique per user — seeder idempotency key
    title: Mapped[str]
    description: Mapped[str | None]
    status: Mapped[str]                  # TRACK_STATUSES
    start_date: Mapped[date | None]
    target_date: Mapped[date | None]
    weekly_hours_target: Mapped[int]     # 11
    sort_order: Mapped[int]
    created_at / updated_at


class LearningConcept(Base):
    __tablename__ = "learning_concepts"

    id: Mapped[str]
    user_id: Mapped[str]
    item_id: Mapped[str]                 # FK learning_items.id (the phase), indexed
    slug: Mapped[str]                    # unique per item
    title: Mapped[str]                   # "autoregressive decode loop"
    summary: Mapped[str | None]
    week_number: Mapped[int | None]      # 1..24
    estimated_minutes: Mapped[int | None]
    sort_order: Mapped[int]
    # --- depth gate ---
    confidence: Mapped[int]              # 0-5, rolled up from sessions
    can_explain: Mapped[bool]            # the actual gate
    failure_modes_known: Mapped[bool]
    tradeoffs_known: Mapped[bool]
    artifact_url: Mapped[str | None]
    completed_at: Mapped[datetime | None]
    created_at / updated_at


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[str]
    user_id: Mapped[str]
    item_id: Mapped[str | None]          # phase-level resource
    concept_id: Mapped[str | None]       # concept-level resource
    resource_type: Mapped[str]           # RESOURCE_TYPES
    title: Mapped[str]
    url: Mapped[str]
    provider: Mapped[str | None]         # "krishnaik06" | "freecodecamp" | "deeplearning.ai"
    author: Mapped[str | None]
    duration_minutes: Mapped[int | None]
    priority: Mapped[str]                # RESOURCE_PRIORITY
    sort_order: Mapped[int]
    is_consumed: Mapped[bool]
    notes: Mapped[str | None]
    last_verified_at: Mapped[date | None]  # link-rot tracking
    created_at / updated_at


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[str]
    user_id: Mapped[str]
    item_id: Mapped[str]                 # FK learning_items.id
    concept_id: Mapped[str | None]       # FK learning_concepts.id
    session_date: Mapped[date]
    minutes: Mapped[int]
    confidence: Mapped[int]              # 1-5, self-rated
    can_explain: Mapped[bool]
    artifact_url: Mapped[str | None]
    notes: Mapped[str | None]            # written in own words — the retention mechanism
    created_at
```

### Change to existing table

```python
class LearningItem(Base):
    ...
    track_id: Mapped[str | None]   # NULL = standalone item (all existing rows) — backward compatible
    sort_order: Mapped[int]        # phase ordering within a track, default 0
```

Two fields do the real work: **`can_explain`** is the depth gate (confidence alone is noise — everyone self-rates 4 the day they read something) and **`artifact_url`** enforces the "every topic must ship code" rule.

`LearningItem.progress` must roll up from `count(concepts where can_explain) / count(concepts)` — **not** from time spent.

### Reuse, don't rebuild

| Need | Use existing |
|---|---|
| Daily study streak | `habits` module — `stats.py` already computes streaks |
| Scheduled study blocks | `routines` module — already has `area="learning"` |
| Deep notes per concept | `knowledge_notes` — subject → chapter → section |
| Quarterly objective | `goals` with `category="learning"` |
| Interview Q&A drilling | `qa` module — type `"Learning"`, has version history |

## 2.4 Seeding — the extensibility mechanism

```
backend/app/modules/learning/seeds/
  ai-systems-engineering.json     # this track
  _schema.json                    # JSON schema for validation
  README.md                       # "how to add a track"
```

Seed shape:

```json
{
  "slug": "ai-systems-engineering",
  "title": "AI Systems Engineering",
  "weekly_hours_target": 11,
  "phases": [
    {
      "slug": "p1-llm-foundations",
      "title": "Phase 1 — LLM Foundations",
      "item_type": "study_plan",
      "sort_order": 1,
      "concepts": [
        {
          "slug": "autoregressive-decode-loop",
          "title": "The LLM as a stateless next-token function",
          "week_number": 1,
          "estimated_minutes": 90,
          "resources": [
            {
              "resource_type": "video",
              "title": "Intro to Large Language Models",
              "url": "https://www.youtube.com/watch?v=zjkBMFhNj_g",
              "provider": "youtube",
              "author": "Andrej Karpathy",
              "duration_minutes": 60,
              "priority": "primary"
            }
          ]
        }
      ]
    }
  ]
}
```

**Seeder contract (this is what makes future tracks free):**

- Idempotent, keyed on `slug` at every level — re-running updates, never duplicates
- Never overwrites user progress fields (`confidence`, `can_explain`, `artifact_url`, `is_consumed`, `notes`, `completed_at`)
- Validates against `_schema.json` before writing
- Exposed as `POST /api/v1/learning/tracks/seed` (body: `{"slug": "..."}`) **and** a CLI entry point
- Adding a new track = **drop in one JSON file**, no code change

## 2.5 API surface

```
GET    /api/v1/learning/tracks
POST   /api/v1/learning/tracks
GET    /api/v1/learning/tracks/{id}                  # nested: phases → concepts → resources
POST   /api/v1/learning/tracks/seed
GET    /api/v1/learning/tracks/{id}/progress         # % complete, hours, streak, pace vs target

GET    /api/v1/learning/concepts?item_id=&week=
PATCH  /api/v1/learning/concepts/{id}                # confidence, can_explain, artifact_url

GET    /api/v1/learning/resources?concept_id=
POST   /api/v1/learning/resources                    # add ad-hoc link found mid-study
PATCH  /api/v1/learning/resources/{id}               # mark consumed

GET    /api/v1/learning/sessions?from=&to=
POST   /api/v1/learning/sessions                     # the daily log
GET    /api/v1/learning/sessions/stats               # minutes/week, pace, concepts gated
```

## 2.6 Wiring checklist (the six registration points)

- [ ] `backend/app/main.py` — router already registered; new endpoints go on existing `learning_router`
- [ ] `frontend/src/app/app.routes.ts` — add `/learning/tracks`, `/learning/tracks/:id`, `/learning/today`
- [ ] `frontend/src/app/shared/layout/nav-registry.ts` — `learning` entry exists; consider adding to `DEFAULT_PINNED_IDS`
- [ ] `backend/app/modules/ai/indexer.py` — index concepts + session notes so the assistant can answer "what did I learn about RRF?"
- [ ] `backend/app/modules/search/` — add `LearningItem` / `LearningConcept` (**currently missing entirely**)
- [ ] `backend/app/modules/export/` — add `learning` to `EXPORT_MODULES` (**currently missing**)

Optional: dashboard widget (today's concept + streak), `predictions` already has `learning_consistency`.

## 2.7 UI constraints

Per `.cursor/rules/ui-style.mdc` — reuse the Ubuntu/Yaru design tokens in `frontend/src/styles.css` (`--primary: #E95420`), existing `.panel` / `.btn-primary` / `.input-field` classes, Lucide icons, Angular signals. Extend `learning-page.component.ts` rather than inventing new layout patterns. No new design language, no decorative animation.

Three views only:

1. **Track view** — phases as collapsible sections, concepts as rows with a confidence chip
2. **Today view** — this week's concepts, resource links, one-tap session log
3. **Concept detail** — resources list, session history, artifact link, the four depth-gate checkboxes

## 2.8 Tests

- `backend/app/tests/test_learning_track.py` — seeder idempotency (run twice → same counts), progress rollup, user isolation
- Extend `test_phase2.py::test_learning_crud` for `track_id` backward compatibility (existing rows keep `track_id = NULL`)

---

# PART 3 — KICKOFF PROMPTS

## 3.1 Implementation prompt (paste into Agent mode to build the module)

```
Implement the LifeOS learning-track extension specified in requirements/08Aug.md (Part 2).

Scope: EXTEND the existing `learning` module. Do not create a new module.
Follow the existing convention exactly: models.py → repository.py → service.py →
schemas.py → api.py, async SQLAlchemy 2.0, Pydantic v2, FastAPI.

Backend:
1. Add LearningTrack, LearningConcept, LearningResource, StudySession to
   backend/app/modules/learning/models.py per the spec in Part 2.3.
2. Add nullable track_id + sort_order to LearningItem. Existing rows must keep
   track_id = NULL and continue working unchanged.
3. Repository/service/schemas for each entity, scoped by user_id like every other module.
4. Idempotent seeder keyed on slug at every level. It must NEVER overwrite user
   progress fields (confidence, can_explain, artifact_url, is_consumed, notes,
   completed_at). Validate input against seeds/_schema.json.
5. Endpoints per Part 2.5, on the existing learning_router.
6. LearningItem.progress rolls up from can_explain ratio, not time spent.

Seed data:
7. Create backend/app/modules/learning/seeds/ai-systems-engineering.json with all
   10 phases, the week-1..24 concepts, and every resource listed in Part 1.3 of
   requirements/08Aug.md. Set last_verified_at to 2026-08-08.
8. Create seeds/_schema.json and seeds/README.md explaining how to add a new track
   by dropping in one JSON file.

Frontend:
9. Extend frontend/src/app/features/learning/ with three views: track, today,
   concept detail. Reuse the Ubuntu/Yaru tokens in styles.css and the existing
   .panel / .btn-primary / .input-field classes and Lucide icons. Angular signals,
   standalone components, lazy routes. No new design language.
10. Register routes in app.routes.ts.

Wiring:
11. Complete the checklist in Part 2.6 — including the AI indexer, and search +
    export, which currently omit learning entirely.

Tests:
12. backend/app/tests/test_learning_track.py — seeder idempotency (run twice,
    assert identical counts and preserved progress), progress rollup, user isolation.
13. Extend test_phase2.py::test_learning_crud for track_id backward compatibility.

Constraints:
- Minimal, focused changes. Do not redesign existing UI.
- No new dependencies unless unavoidable — justify any you add.
- Run the backend test suite before reporting done.
```

## 3.2 Daily mentor prompt (paste at the start of each study session)

```
You are my Senior AI Engineer / AI Systems Architect mentor.
Plan of record: requirements/08Aug.md. I am on Week {N}, Phase {P}, concept "{CONCEPT}".

Teach ONE concept only. Structure:
1. Simple intuition
2. Analogy mapped to backend/distributed systems (payments, Kafka, ledgers, K8s)
3. Formal explanation + internal mechanics
4. When to use / when NOT to / alternatives / trade-offs
5. Failure modes
6. Production: cost, latency, scalability, security, observability
7. Where it appears (or is missing) in LifeOS's backend/app/modules/ai/
8. Long-lived concept vs current implementation vs vendor-specific — say which parts will age out

Then STOP and ask me 4-6 senior-level questions: conceptual, debugging, trade-off,
architecture. Do NOT give answers until I have attempted them.

If my answer is weak: say what is missing, give the ideal answer, explain why it
matters, then ask a harder follow-up.

Do not advance until I can (a) explain it without notes, (b) name two failure modes,
(c) state the trade-off vs the alternative, (d) show a working artifact.

I am not a beginner in software engineering. Do not explain HTTP, queues, retries,
idempotency or containers to me. Connect new ideas to what I already know.
```

## 3.3 Weekly review prompt (Sunday)

```
Weekly review against requirements/08Aug.md. I am closing Week {N}.

Concepts covered: {list}
Artifacts shipped: {links}
Hours logged: {n}

1. Quiz me on 3 concepts from THIS week and 2 from ANY earlier week (spaced repetition).
2. Review my artifact as a senior engineer would in code review — correctness,
   failure modes, cost, observability.
3. Tell me honestly whether I have met the depth gate or need another pass.
4. If I am behind pace, tell me what to CUT, not how to rush.
5. Give me next week's plan in one paragraph.
```

---

## Open items

- [ ] Answer the five Week-1 questions on the autoregressive decode loop (asked in chat 08 Aug)
- [ ] Run §3.1 in Agent mode to build the module
- [ ] Week 1 deliverable: instrument `OpenAiProvider` with token/latency/cost logging
- [ ] Monthly: re-verify resource URLs, update `last_verified_at`

## Notes

- Resource links verified 08 Aug 2026. Playlist IDs and course URLs drift — they live in seed JSON, not code, so correcting them is a data edit.
- Phase 5 (frameworks) and the MCP spec are the fastest-ageing sections here. The concepts underneath them are not.
- Sheryians AI School is included at `priority: optional` only. See §1.3 for why.
