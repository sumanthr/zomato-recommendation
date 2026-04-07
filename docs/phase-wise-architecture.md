# Zomato AI Recommendation System - Phase-wise Architecture

## As-built implementation (current repository)

This section describes what is implemented today so the narrative below stays aligned with code.

- **Repository layout**: Phase-isolated code under `src/phases/phase_0/` … `phase_7/`; tests under `tests/`; data under `data/raw`, `data/processed`, `data/reports`.
- **Dataset**: Hugging Face `ManikaSaini/zomato-restaurant-recommendation` (train split). Optional local raw path via `ZOMATO_LOCAL_RAW_PATH` if download is blocked.
- **Phase 1 curation**: Raw columns are mapped to canonical fields, including HF-specific names: `name` → name; `location` → locality; `listed_in(city)` → city; `rate` → rating; `approx_cost(for two people)` → `avg_cost_for_two`. Output: `data/processed/restaurants.parquet` (row count depends on cleaning/dedup rules).
- **Phase 2 retrieval**: Filters by **locality** (exact match first, then fuzzy against inventory), **minimum rating**, **cuisine** (substring match on parsed cuisine list; limited synonym map—no broad collapsing of regional Indian labels into a single tag), and **budget**. **Numeric budget** is treated as **maximum cost for two** (`avg_cost_for_two` in `0..budget`). **Categorical** `low` / `medium` / `high` uses fixed bands in `src/phases/phase_2/config.py`. Default path is **strict** retrieval only (no irrelevant backfill). `GET /localities` and `GET /dataset-summary` expose inventory and counts.
- **Phase 3 LLM**: Groq via `GROQ_API_KEY` and `LLM_MODEL` in `.env`. When the candidate set is large or the provider fails, the service uses **deterministic ranking** from retrieval scores; output is **deduplicated** by `(restaurant_name, locality)` to avoid duplicate cards for multi-branch brands.
- **Phase 4 API**: FastAPI app in `src/phases/phase_4/api.py` — `POST /recommendations`, `GET /health`, `GET /metrics`, `GET /localities`, `GET /dataset-summary`; CORS via `ALLOWED_ORIGINS` / dev defaults.
- **Phase 5 UI**: React (Vite) in `src/phases/phase_5/frontend` — locality **dropdown**, numeric budget, cuisine, minimum rating; internal `top_k` up to schema max (see contracts). Cards show **locality, cuisine, rating, cost**; no separate “craving” search bar, chips, or refine buttons in the current UI.

The sections below remain the **target / design** narrative; where they differ from as-built, **as-built wins** for behavior and deployment.

---

## 1) Vision, Scope, and Success Criteria

### Purpose
Build an AI-powered restaurant recommendation application that combines:
- Structured filtering (location, budget, cuisine, rating)
- LLM reasoning and ranking
- Human-like explanation generation

### What this system should do well
- Return relevant recommendations quickly and reliably.
- Provide transparent reasons for each suggestion.
- Handle ambiguous user preferences with graceful defaults.
- Be easy to extend with new constraints (dietary, ambiance, delivery time).

### Phase success metrics
- Relevance: at least 70%+ user acceptance in basic feedback tests.
- Latency: <= 3s p95 for recommendation response in MVP.
- Reliability: 99%+ successful API responses.
- Explainability: every result contains a machine and human-readable rationale.

---

## 2) End-to-End Target Architecture (Final State)

### Logical layers
1. **Data Layer**
   - Zomato dataset ingestion from Hugging Face
   - Cleaning, normalization, feature engineering
   - Storage in analytic + serving stores

2. **Retrieval and Candidate Generation Layer**
   - Fast rule-based filtering on structured features
   - Optional semantic retrieval for free-text preferences

3. **LLM Recommendation Layer**
   - Prompt builder with candidate context
   - LLM-based ranking + explanation generation
   - Guardrails and output schema validation

4. **Application Layer**
   - Backend API to receive user preferences
   - Recommendation orchestration service
   - Caching and observability

5. **Experience Layer**
   - Web UI/CLI for preference input
   - Ranked recommendation cards with explanation

6. **MLOps + Platform Layer**
   - Experiment tracking and evaluation
   - Monitoring, retries, deployment automation

### Core runtime flow
1. User submits preferences.
2. Backend validates and normalizes input.
3. Candidate generator retrieves top N restaurants.
4. Prompt composer sends candidates + user needs to LLM.
5. LLM returns ranked results and reasons in strict JSON schema.
6. Post-processor verifies constraints and finalizes top K output.
7. UI renders recommendations with key fields + explanations.
8. Interaction logs feed evaluation and improvement loop.

---

## 3) Phase-wise Build Plan

## Phase 0 - Foundation and Project Setup

### Goals
- Establish repository structure, coding standards, and initial tooling.
- Lock architecture decisions for MVP and scale path.

### Deliverables
- Standard folder layout:
  - `data/` (raw, interim, processed)
  - `src/phases/phase_0/` … `src/phases/phase_7/` (contracts, ingestion, retrieval, LLM, API, UI, eval, deploy helpers)
  - `configs/` for env and model configs
  - `tests/` for unit/integration/e2e
- `.env.example` and secret management approach.
- Initial README with local setup and run commands.

### Technical decisions
- Backend framework: FastAPI (recommended for speed + typed APIs).
- Data processing: Pandas (MVP), move to Polars/Spark only if scale demands.
- LLM provider abstraction: wrapper interface (`generate_recommendations()`).
- Output schema: strict JSON contract to avoid brittle parsing.

### Exit criteria
- Project boots locally with placeholder API endpoint.
- CI checks (lint + tests) pass on empty skeleton.

---

## Phase 1 - Data Ingestion and Data Quality Pipeline

### Goals
- Build a repeatable ingestion process from Hugging Face dataset.
- Produce clean, normalized restaurant records.

### Tasks
1. **Dataset connector**
   - Pull dataset snapshot from Hugging Face.
   - Version dataset metadata (source URL, date, record count).

2. **Schema mapping**
   - Map raw columns to canonical schema (Hugging Face column names in parentheses where applicable):
     - `restaurant_id`
     - `name` (from `name`)
     - `location_city` (from `listed_in(city)`), `locality` (from `location`)
     - `cuisines` (list, parsed from `cuisines`)
     - `avg_cost_for_two` (from `approx_cost(for two people)`)
     - `rating` (from `rate`)
     - optional text features (highlights/reviews)

3. **Cleaning and normalization**
   - Handle nulls and malformed values.
   - Normalize city and cuisine names (lowercase dictionary mapping).
   - Convert rating and cost to numeric ranges.
   - Deduplicate restaurants by logical key.

4. **Data quality checks**
   - Null-rate thresholds for critical fields.
   - Outlier detection for cost and rating.
   - Basic schema validation (Pydantic/Pandera).

5. **Persist curated dataset**
   - Save processed table to `data/processed/restaurants.parquet`.
   - Export lightweight serving format (`jsonl` or sqlite table).

### Exit criteria
- One command reproduces curated data from source.
- Data quality report generated and stored.

---

## Phase 2 - Feature Engineering and Candidate Retrieval

### Goals
- Build deterministic candidate shortlist before calling the LLM.
- Ensure recommendations remain relevant and cheap to generate.

### Tasks
1. **Input normalization layer**
   - Budget categories:
     - `low`, `medium`, `high` -> cost ranges
   - Numeric budget support:
     - direct amount for two used as **maximum** `avg_cost_for_two` (not only coarse bands)
   - Cuisine synonyms:
     - small map for typos/aliases (e.g. fast food, italian); avoid collapsing distinct regional tags into one bucket
   - Locality: exact match when possible, else fuzzy match against curated inventory.

2. **Structured filter engine**
   - Apply must-have constraints:
     - location match
     - minimum rating
     - budget range
     - cuisine overlap
   - Rank candidates by weighted formula:
     - score = `w1*rating + w2*cuisine_match + w3*budget_fit + w4*popularity`

3. **Fallback strategy (as-built)**
   - Primary behavior: **strict** filters only; if no matches, return empty candidates with `no_candidates` tier (no irrelevant global backfill).
   - Optional relaxed tiers may exist in config for experiments; production UX assumes strict relevance.

4. **Optional semantic retrieval (Phase 2.5)**
   - For additional text preferences (e.g., "family-friendly"):
     - Generate embeddings for restaurant descriptors.
     - Retrieve nearest neighbors and blend with structured ranking.

### Exit criteria
- Candidate generation returns 20-100 records for typical query.
- Retrieval latency <= 300ms locally for MVP dataset size.

---

## Phase 3 - LLM Recommendation Engine

### Goals
- Convert candidate list into personalized, explainable top recommendations.
- Keep output stable, structured, and constraint-aware.

### Tasks
1. **Prompt template design**
   - System instruction: role + constraints + tone.
   - User section: normalized preferences.
   - Candidate section: compact, token-efficient table/list.
   - Output schema section: strict JSON fields required.
   - Use Groq chat completion models for Phase 3 prompt execution.

2. **Recommendation strategy**
   - Ask LLM to:
     - rank top K
     - explain each recommendation relative to user preferences
     - mention trade-offs when constraints conflict

3. **Schema-constrained output**
   - Required fields per recommendation:
     - `restaurant_name`
     - `cuisine`
     - `rating`
     - `estimated_cost`
     - `explanation`
     - `fit_score` (0-100)
   - Parse with strict validator and retry on malformed response.

4. **Guardrails**
   - Prevent hallucinated restaurants:
     - LLM may only pick from candidate IDs passed in context.
   - Post-check ensures name/ID exists in candidate set.
   - Safety filters for inappropriate content.

5. **Cost and latency optimization**
   - Candidate compression (only essential fields).
   - Cache responses for repeated queries.
   - Tune model choice by environment:
     - larger model for offline eval
     - faster model for production API

6. **Provider and secrets**
   - LLM provider: Groq.
   - API key source: `.env` file using `GROQ_API_KEY`.
   - Model config source: `.env` using `LLM_MODEL`.

### Exit criteria
- 95%+ responses parse correctly into schema.
- No out-of-candidate hallucinations in test runs.

---

## Phase 4 - API and Orchestration Service

### Goals
- Expose recommendation capability via stable backend endpoints.
- Implement robust orchestration from input to final response.

### Core API design
- `POST /recommendations`
  - input:
    - `location` (locality)
    - `budget` (numeric max for two, or `low` | `medium` | `high`)
    - `cuisine`
    - `minimum_rating`
    - `additional_preferences` (optional)
    - `top_k` (default 50 in schema; max 200; often fixed in UI)
  - output:
    - normalized input
    - ranked recommendations (includes `locality` per item when available)
    - metadata (`prompt_version`, `model_version`, `data_version`, `fallback_tier`)

- `GET /health`
- `GET /metrics`
- `GET /localities` — dropdown inventory from curated data
- `GET /dataset-summary` — restaurant / locality / city counts

### Orchestration workflow
1. Validate request schema.
2. Normalize and enrich preferences.
3. Retrieve candidate pool.
4. Build prompt and call LLM provider.
5. Validate/repair output.
6. Return response with diagnostics metadata.

### Reliability patterns
- Timeouts for external LLM calls.
- Circuit breaker + fallback summary when LLM unavailable.
- Request/response tracing using request IDs.

### Exit criteria
- End-to-end API works with test payloads.
- Error handling covers invalid input + provider failures.

---

## Phase 5 - User Interface and Experience

### Goals
- Provide simple, intuitive interaction for non-technical users.
- Make recommendation rationale visible and trustworthy.

### MVP UI components (as-built)
- Preference form:
  - Locality dropdown (loaded from backend locality inventory)
  - Amount for two (numeric input)
  - Cuisine text input
  - Minimum rating numeric input
- Results panel:
  - Recommendation cards (name, locality, cuisine, rating, cost)
  - Empty state: “No restaurants found” when there are no matches

### UX enhancements
- Loading states; clear empty state; no mandatory “refine” or top “craving” search bar in current build.

### Exit criteria
- User can complete request in < 4 interactions.
- Recommendations are readable and actionable.

---

## Phase 6 - Evaluation, Feedback Loop, and Quality Tuning

### Goals
- Measure recommendation quality, not just system uptime.
- Build loop for iterative improvements.

### Evaluation framework
1. **Offline tests**
   - Curated user scenarios (location-budget-cuisine combinations).
   - Relevance scoring rubric:
     - constraint satisfaction
     - quality of explanation
     - diversity of suggestions

2. **Online feedback**
   - Collect thumbs up/down per recommendation set.
   - Optional reason tags: "too expensive", "wrong cuisine", "far away".

3. **Metrics dashboard**
   - Acceptance rate
   - Fallback rate
   - LLM parse failure rate
   - p50/p95 latency
   - Cost per 100 requests

### Improvement levers
- Tune candidate weights.
- Improve prompt examples.
- Adjust fallback relaxation order.
- Add better features for additional preferences.

### Exit criteria
- Baseline metrics published and tracked over time.
- At least one closed-loop tuning iteration completed.

---

## Phase 7 - Deployment, Monitoring, and Production Hardening

### Goals
- Make system production-ready with observability and safe rollout.

### Deployment architecture
- Containerized backend service (Docker).
- Managed hosting (Render/AWS/GCP/Azure).
- Optional managed DB for metadata and logs.

### Production components
- CI/CD pipeline:
  - test -> build -> deploy
- Secrets manager for API keys.
- Monitoring + alerting:
  - error rates
  - latency spikes
  - provider failures

### Resilience and governance
- Rate limiting and abuse protection.
- Data retention policy for user inputs.
- Prompt/version registry for reproducibility.
- Canary deployment for model/prompt updates.

### Exit criteria
- Zero-downtime deployment flow validated.
- Alerts configured for core SLO violations.

---

## 4) Suggested Tech Stack by Layer

- **Data ingestion/processing:** Python, Hugging Face Datasets, Pandas, Parquet
- **Serving datastore:** SQLite/PostgreSQL (MVP -> scale path)
- **Backend/API:** FastAPI, Pydantic
- **LLM integration:** Provider SDK via abstraction module
- **UI:** Streamlit (fast MVP) or React + Next.js (scale)
- **Observability:** OpenTelemetry + Prometheus/Grafana (or hosted equivalent)
- **Testing:** Pytest, integration tests, basic load tests

---

## 5) Recommended Repository Blueprint

- `src/ingestion/` - download and normalize dataset
- `src/features/` - schema transforms and feature logic
- `src/retrieval/` - structured filter and ranking
- `src/llm/` - prompt templates, provider client, output parser
- `src/service/` - orchestration pipeline
- `src/api/` - FastAPI routes and request/response models
- `src/ui/` - front-end app
- `src/evals/` - offline scenario definitions and scoring
- `configs/` - model, prompt, and environment config
- `tests/` - unit/integration/e2e tests

---

## 6) Milestone Timeline (Practical Sequence)

1. **Week 1:** Phase 0 + Phase 1 (setup + ingestion pipeline)
2. **Week 2:** Phase 2 (candidate retrieval and fallbacks)
3. **Week 3:** Phase 3 + Phase 4 (LLM engine + API orchestration)
4. **Week 4:** Phase 5 + Phase 6 (UI + evaluation loop)
5. **Week 5:** Phase 7 (deployment and hardening)

---

## 7) Risks and Mitigations

- **Sparse/dirty dataset fields**
  - Mitigation: strict quality checks + robust defaults.
- **LLM hallucinations**
  - Mitigation: candidate-only constraint + schema validation.
- **High inference cost**
  - Mitigation: pre-filtering + caching + model tiering.
- **Latency spikes**
  - Mitigation: timeouts, async calls, prompt token minimization.
- **Weak recommendation trust**
  - Mitigation: explicit reasoning tied to user preferences.

---

## 8) Immediate Next Implementation Steps

1. Implement ingestion script to create `data/processed/restaurants.parquet`.
2. Define canonical schema and validation models.
3. Build deterministic candidate filtering API.
4. Add first LLM prompt template with strict JSON output.
5. Expose `POST /recommendations` and validate with sample scenarios.

