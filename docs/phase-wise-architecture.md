# Zomato AI Recommendation System - Phase-wise Architecture

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
  - `src/ingestion/`, `src/features/`, `src/recommender/`, `src/api/`, `src/ui/`
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
   - Map raw columns to canonical schema:
     - `restaurant_id`
     - `name`
     - `location_city`, `locality`
     - `cuisines` (list)
     - `avg_cost_for_two`
     - `rating`
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
     - direct amount for two (for example `1200`) mapped to bands dynamically
   - Cuisine synonyms:
     - `north indian`, `indian`
     - `fast-food`, `quick bites`
   - Fuzzy match locality (primary input) and not only city.

2. **Structured filter engine**
   - Apply must-have constraints:
     - location match
     - minimum rating
     - budget range
     - cuisine overlap
   - Rank candidates by weighted formula:
     - score = `w1*rating + w2*cuisine_match + w3*budget_fit + w4*popularity`

3. **Fallback strategy**
   - If candidate pool too small:
     - relax constraints in defined order (budget -> cuisine -> locality).
   - Record fallback reason for transparency.
   - If returned candidates are still fewer than `top_k`, fill from a global high-quality pool
     (minimum rating matched, de-duplicated) to always return a useful list.

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
    - `location`
    - `budget`
    - `cuisine`
    - `minimum_rating`
    - `additional_preferences`
    - `top_k` (default 5)
  - output:
    - normalized input
    - ranked recommendations
    - metadata (latency, fallback_used, model_version)

- `GET /health`
- `GET /metrics` (if Prometheus style monitoring is enabled)

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

### MVP UI components
- Preference form:
  - Locality dropdown (loaded from backend locality inventory)
  - Amount for two (numeric input)
  - Cuisine selector
  - Minimum rating slider
  - Additional preferences free-text
- Results panel:
  - Recommendation cards (name, cuisine, rating, cost)
  - AI explanation
  - "Why this matches you" highlights

### UX enhancements
- Loading states and skeleton cards.
- Empty-state suggestions (when no strong matches).
- Optional "refine your search" chips.

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

