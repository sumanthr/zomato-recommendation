# Zomato AI Recommendation - Revalidated Phase-wise Architecture

## As-built alignment (summary)

The repository implements the hybrid pattern end-to-end with **phase folders** under `src/phases/`. Key behavioral choices that differ from earlier drafts:

| Area | As-built behavior |
|------|-------------------|
| Phase 1 | HF dataset `ManikaSaini/zomato-restaurant-recommendation`; map `location`→locality, `listed_in(city)`→city, `rate`→rating, `approx_cost(for two people)`→cost |
| Phase 2 | Strict filtering by locality, rating, cuisine overlap, budget; numeric budget = max cost for two; locality exact-then-fuzzy |
| Phase 3 | Groq LLM optional; deterministic ranking + dedupe by name+locality when needed |
| Phase 4 | FastAPI: `/recommendations`, `/health`, `/metrics`, `/localities`, `/dataset-summary`, CORS |
| Phase 5 | React form + cards; no refine/craving bar; shows locality on cards |

See also `docs/phase-wise-architecture.md` **As-built implementation** for the same facts in prose.

---

## 1) Revalidated Strategy (Why this architecture is right)

This architecture intentionally uses a **hybrid recommender pattern**:
- **Deterministic retrieval first** (structured filters and scoring), then
- **LLM reasoning second** (personalization and explanation).

### Why this is the right strategy
- It keeps recommendations grounded in real dataset records.
- It reduces hallucination and cost by limiting LLM context to shortlisted candidates.
- It improves latency and reliability because heavy reasoning is done only on a small candidate set.
- It gives clear control points (weights, fallback rules, filters) that can be tuned without retraining.

### What is changed after revalidation
- Added stricter **contract-first design**: request schema, candidate schema, and response schema are frozen early.
- Added **quality gates** per phase to avoid proceeding with hidden issues.
- Added explicit **fallback modes** (no-result, low-confidence, provider failure) with user-safe behavior.
- Added **evaluation earlier** (from Phase 2 onward), not only after UI completion.

---

## 2) Reference Architecture (System View)

### A) Data Plane
- Ingestion jobs load and normalize restaurant data.
- Feature tables power retrieval and ranking.
- Optional embedding index supports text preference matching.

### B) Control Plane
- Configs for prompt versions, scoring weights, and fallback policy.
- Experiment toggles for A/B testing (prompt A vs B, strict vs relaxed retrieval).

### C) Request Plane
- API receives user preferences.
- Orchestrator runs normalize -> retrieve -> LLM rank/explain -> validate -> return.

### D) Observability Plane
- Structured logs, traces, and quality metrics.
- Offline/online evaluation loops tied to prompt/model/version.

---

## 3) Phase-by-Phase Architecture (Why, What, How)

## Phase 0 - Foundation and Contract Design

### Why
Early ambiguity in schema and interfaces is the biggest source of downstream rework. This phase prevents that by defining contracts first.

### What
- Repo structure and coding conventions.
- API contracts and data contracts.
- Baseline configuration strategy.
- Local dev, test, and CI bootstrap.

### How
1. Define canonical typed models:
   - `UserPreferenceInput`
   - `RestaurantRecord`
   - `CandidateRecord`
   - `RecommendationResponse`
2. Freeze JSON schema and example payloads in `docs/contracts/`.
3. Set up minimal FastAPI app and test harness.
4. Add environment configuration (`.env.example`, config loader).
5. Add CI checks (lint, unit tests).

### Quality gate
- Every contract has a sample valid/invalid payload test.
- CI passes on fresh clone.

---

## Phase 1 - Data Ingestion, Curation, and Trust Layer

### Why
Recommendation quality is constrained by data quality. Bad normalization leads to bad retrieval and irrelevant outputs.

### What
- Repeatable ingestion from Hugging Face.
- Canonical schema mapping.
- Cleaning and normalization for city/cuisine/cost/rating.
- Data quality report + lineage metadata.

### How
1. Build `ingest_zomato.py`:
   - Pull dataset snapshot and stamp metadata.
2. Build `curate_restaurants.py`:
   - Standardize city/locality labels.
   - Parse cuisine strings into arrays.
   - Convert rating/cost to numeric safe ranges.
   - Remove duplicates.
3. Generate artifacts:
   - `data/processed/restaurants.parquet`
   - `data/processed/restaurants_serving.jsonl`
   - `data/reports/data_quality.json`
4. Add quality checks:
   - null thresholds on critical columns
   - invalid type thresholds
   - value range checks

### Quality gate
- Reproducible run: same input snapshot -> same curated output hash.
- Data quality report meets pre-defined thresholds.

---

## Phase 2 - Deterministic Retrieval and Candidate Scoring

### Why
LLM should not search the full dataset. Retrieval provides relevance, explainability, speed, and cost control.

### What
- Preference normalization and synonym resolution.
- Hard filters + soft scoring.
- Fallback policy for sparse results.

### How
1. Input normalization service:
   - accept numeric amount-for-two as **maximum** cost for two (strict filter), or categorical `low`/`medium`/`high` mapped to configured bands
   - map a **small** cuisine synonym set (typos/aliases); do not merge distinct regional cuisines into one tag
   - match locality: **exact** (case-insensitive) first, else fuzzy against curated inventory
2. Hard constraints:
   - locality, min rating, budget (numeric max or band), cuisine overlap on parsed list
3. Soft scoring:
   - cuisine overlap score
   - rating score
   - budget-fit score
   - popularity/proxy score
4. Fallback tiers (as-built default):
   - **Strict only** for relevance; empty result if nothing matches (`no_candidates`). Relaxed tiers are optional/experimental, not used to fill irrelevant rows in the default product path.
5. Candidate bundle contract:
   - top N with compact fields + score breakdown; candidates include **locality** for display and deduplication

### Quality gate
- Candidate recall tests pass on curated test scenarios.
- p95 retrieval latency target met.
- Fallback reason always emitted when relaxation is applied.

---

## Phase 3 - LLM Ranking and Explanation Layer

### Why
Deterministic scoring alone feels mechanical; LLM adds nuanced ordering and human-readable rationale.

### What
- Prompt architecture with strict constraints.
- Structured response generation (JSON schema).
- Guardrails against hallucinations and invalid outputs.
- Groq as the fixed LLM provider for Phase 3.

### How
1. Prompt template sections:
   - role and task
   - user preference summary
   - allowed candidates (ID-locked)
   - ranking rules and trade-off behavior
   - output schema and tone
2. Enforce candidate lock:
   - prompt says only choose candidate IDs listed
   - post-validator rejects unknown IDs
3. Structured parser and retries:
   - parse -> validate -> repair retry -> fail-safe fallback
4. Confidence tagging:
   - assign confidence based on filter strictness and match quality
5. Safe fallback response:
   - deterministic top-K from retrieval scores if LLM fails or candidate count is large; deduplicate by `(name, locality)`; explanations may be omitted in UI even if present in API schema
6. Provider configuration:
   - load `GROQ_API_KEY` from `.env`
   - load model name from `LLM_MODEL` in `.env`

### Quality gate
- Schema parse success rate >= target.
- Zero hallucinated candidate IDs in regression suite.
- Fallback path returns valid response for simulated provider outages.

---

## Phase 4 - Orchestration API and Service Reliability

### Why
A strong recommender needs consistent behavior under variable traffic and external API instability.

### What
- Production-style endpoint behavior.
- End-to-end orchestration with diagnostics.
- Resilience controls.

### How
1. Implement endpoints:
   - `POST /recommendations`
   - `GET /health`
   - `GET /metrics`
   - `GET /localities`
   - `GET /dataset-summary`
2. Orchestration pipeline:
   - validate input
   - normalize input
   - retrieve candidates
   - invoke LLM
   - validate output
   - return with metadata
3. Reliability controls:
   - timeout budgets per stage
   - retry with jitter for transient LLM failures
   - circuit breaker on repeated provider failures
4. Diagnostics metadata:
   - request_id
   - prompt_version
   - model_version
   - fallback_tier
   - stage latencies

### Quality gate
- Integration tests pass across happy path + error path.
- Load test meets p95 latency and error targets for expected QPS.

---

## Phase 5 - UX Layer (Form, Result Cards)

### Why
Even high-quality recommendations fail adoption if input is confusing or output is hard to interpret.

### What
- Preference capture experience.
- Result rendering with dataset-grounded fields (locality visible so multi-branch brands are understandable).

### How
1. Build form with guided controls:
   - locality dropdown, numeric amount-for-two, cuisine, min rating
2. Render recommendation cards:
   - name, locality, cuisine, rating, estimated cost (explanation line optional / hidden in UI per product choice)
3. Handle non-ideal states:
   - empty result message (“No restaurants found”)
   - loading and error UX

### Quality gate
- Usability run: user reaches a recommendation in <= 4 interactions.
- Empty and low-confidence flows are understandable in user tests.

---

## Phase 6 - Evaluation System and Continuous Improvement

### Why
Without measurable quality loops, recommendation systems drift and regress silently.

### What
- Offline benchmark suite.
- Online feedback capture.
- Tuning protocol for retrieval and prompts.

### How
1. Offline benchmark creation:
   - 50-100 scenario set with expected characteristics
2. Auto-scoring dimensions:
   - constraint adherence
   - ranking quality proxy
   - explanation quality rubric
3. Online telemetry:
   - thumbs up/down
   - reason tags
   - abandonment events
4. Tuning cadence:
   - weekly weight updates
   - prompt revision with versioning
   - regression test before release

### Quality gate
- Baseline metrics published.
- At least one tuning iteration improves target KPI(s) without latency regression.

---

## Phase 7 - Production Hardening and Scale Path

### Why
MVP success creates real traffic and operational pressure; scale-readiness avoids outages and cost spikes.

### What
- Deployment pipeline and runtime hardening.
- Cost governance and security controls.
- Controlled rollout for model/prompt changes.

### How
1. Deploy backend service on Streamlit with health checks and runtime monitoring.
2. Deploy frontend on Vercel and point it to the backend API URL.
3. Add auth/rate limiting and secret management.
4. Add budget safeguards:
   - token caps
   - per-request max candidates
   - provider fallback model
5. Rollout strategy:
   - canary by prompt/model version
   - rollback on KPI or error threshold breaches

### Quality gate
- Runbook exists for incident classes (LLM outage, latency spike, bad deployment).
- Canary rollout and rollback validated in staging.

---

## 4) Cross-cutting Design Decisions (Must remain consistent)

1. **Schema-first everywhere**
   - Inputs, intermediate candidates, and outputs are typed and validated.
2. **Deterministic before generative**
   - LLM never replaces core retrieval truth.
3. **Explicit fallbacks**
   - Never return an opaque failure; always provide best-possible response.
4. **Version everything**
   - data snapshot, prompt, model, and scoring weights.
5. **Observability by default**
   - every recommendation request is diagnosable.

---

## 5) Implementation Readiness Criteria (Before coding each phase)

For each phase, confirm:
- Objective and non-objective are documented.
- Inputs and outputs are schema-defined.
- Test cases are listed before implementation.
- Exit gate metrics are measurable.
- Dependencies from previous phases are completed.

---

## 6) Remaining Inputs Required for a Solid Finalized Plan

To fully lock the implementation plan, these details are still required:

1. Product and usage assumptions
   - Expected daily active users and peak QPS?
   - MVP audience: demo users, internal users, or public beta?

2. Region and dataset scope
   - Do we support all cities in dataset from day one or only selected cities?
   - Are there mandatory filters (veg-only, delivery-only, open-now)?

3. Budget semantics
   - Exact rupee ranges for `low`, `medium`, `high`?
   - Should budget be per person or for two people?

4. Quality expectations
   - Minimum acceptable relevance KPI at launch?
   - Do you want diversity constraints in top-K (avoid same cuisine repeated)?

5. LLM constraints
   - Preferred provider/model and monthly budget cap?
   - Any requirement for open-source/self-hosted model?

6. UI and platform decisions
   - Streamlit for speed or React for product-grade UX?
   - Hosting preference (AWS/GCP/Azure/Render)?

7. Compliance and logging
   - Can we store raw user preference text and feedback events?
   - Data retention window expectations?

Once these are confirmed, this architecture can be converted into a locked delivery plan with exact estimates and owners.

