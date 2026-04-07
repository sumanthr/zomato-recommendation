# Zomato AI Recommendation - Detailed Execution Checklist

This checklist is implementation-focused and sequenced to build phase-by-phase with clear dependencies, acceptance criteria, and done-definition.

## How to use this checklist

- Mark each task as `[ ]` -> `[x]` when completed.
- Do not start a phase until its entry criteria are met.
- Do not close a phase until all exit checks pass.
- Treat all schema changes as versioned changes.

---

## Phase 0 - Foundation and Contract Setup

### Entry criteria
- [ ] Project repository available on `main`.
- [ ] Python version and package manager decided.

### Architecture and contracts
- [ ] Create canonical request schema `UserPreferenceInput`.
- [ ] Create canonical data schema `RestaurantRecord`.
- [ ] Create candidate schema `CandidateRecord`.
- [ ] Create API response schema `RecommendationResponse`.
- [ ] Add version field to response metadata (`prompt_version`, `model_version`, `data_version`).
- [ ] Document schemas in `docs/contracts/`.

### Project structure and tooling
- [ ] Create directories:
  - [ ] `src/phases/phase_0/` (contracts + API scaffold)
  - [ ] `src/phases/phase_1/` (ingestion + quality)
  - [ ] `src/phases/phase_2/` (retrieval + fallback)
  - [ ] `src/phases/phase_3/` (LLM ranking)
  - [ ] `src/phases/phase_4/` (API orchestration layer)
  - [ ] `src/phases/phase_5/` (UI integration)
  - [ ] `src/phases/phase_6/` (evaluation loop)
  - [ ] `src/phases/phase_7/` (deployment hardening)
  - [ ] `tests/unit/`
  - [ ] `tests/integration/`
  - [ ] `tests/e2e/`
  - [ ] `configs/`
- [ ] Add `.env.example` with non-secret placeholders.
- [ ] Add `README` setup instructions.
- [ ] Add lint, format, and test commands.
- [ ] Configure CI to run lint + tests.

### Validation and sign-off
- [ ] Sample valid request/response payload tests pass.
- [ ] Sample invalid payload tests fail as expected.
- [ ] CI green on clean clone.

### Phase 0 exit criteria
- [ ] Contracts are frozen for Phase 1-3.
- [ ] Team agrees on coding and branching conventions.

---

## Phase 1 - Data Ingestion and Data Quality

### Entry criteria
- [ ] Phase 0 schemas are finalized and versioned.

### Source ingestion
- [ ] Implement Hugging Face dataset downloader.
- [ ] Capture dataset source metadata:
  - [ ] source URL
  - [ ] pull timestamp
  - [ ] row count
  - [ ] schema snapshot
- [ ] Store raw snapshot under `data/raw/`.

### Curation and normalization
- [ ] Implement column mapping to `RestaurantRecord`.
- [ ] Parse and normalize cuisine values to list format.
- [ ] Normalize city/locality strings.
- [ ] Convert rating and cost to numeric types.
- [ ] Handle malformed/null values with deterministic rules.
- [ ] Deduplicate records using deterministic key policy.

### Data quality checks
- [ ] Add null-rate checks for critical columns.
- [ ] Add range checks:
  - [ ] rating bounds
  - [ ] cost bounds
- [ ] Add categorical checks for known fields.
- [ ] Produce machine-readable quality report (`json`).

### Artifacts
- [ ] Save curated table to `data/processed/restaurants.parquet`.
- [ ] Save serving artifact (`jsonl` or sqlite).
- [ ] Save quality report to `data/reports/`.

### Tests
- [ ] Unit tests for normalization functions.
- [ ] Integration test for full ingestion pipeline.
- [ ] Reproducibility test for same input snapshot.

### Phase 1 exit criteria
- [ ] One command rebuilds curated artifacts end-to-end.
- [ ] Quality thresholds pass and are documented.

---

## Phase 2 - Retrieval, Ranking, and Fallbacks

### Entry criteria
- [ ] Curated serving dataset is available and validated.

### Input normalization
- [ ] Implement budget band mapping from numeric amount-for-two and (`low`, `medium`, `high`).
- [ ] Implement cuisine synonym dictionary.
- [ ] Implement fuzzy locality matcher using curated locality inventory.
- [ ] Add normalization confidence score.

### Candidate retrieval
- [ ] Implement hard filter pipeline:
  - [ ] location
  - [ ] min rating
  - [ ] budget
  - [ ] cuisine overlap
- [ ] Implement weighted scoring formula.
- [ ] Expose score breakdown fields per candidate.

### Fallback policies
- [ ] Define and implement fallback tiers:
  - [ ] strict
  - [ ] relaxed budget
  - [ ] relaxed cuisine
  - [ ] widened locality
- [ ] top-k completion fallback (global rated pool) if candidate count is below requested `top_k`
- [ ] Emit `fallback_tier` and `fallback_reason`.
- [ ] Ensure fallback order is configurable.

### Performance
- [ ] Add retrieval latency instrumentation.
- [ ] Add caching for repeated normalized queries (optional for MVP).

### Tests
- [ ] Unit tests for scoring and filter logic.
- [ ] Scenario tests for no-result and low-result cases.
- [ ] Regression tests for synonym and fuzzy matching behavior.

### Phase 2 exit criteria
- [ ] Candidate pool quality verified on benchmark scenarios.
- [ ] Latency targets met for expected dataset size.

---

## Phase 3 - LLM Recommendation Engine

### Entry criteria
- [ ] Candidate generator produces stable top-N with score breakdown.

### Prompt and output contract
- [ ] Set LLM provider to Groq for Phase 3.
- [ ] Add `GROQ_API_KEY` in `.env`.
- [ ] Set `LLM_MODEL` in `.env` (for Groq model selection).
- [ ] Create prompt template v1:
  - [ ] system role and constraints
  - [ ] user preference summary
  - [ ] candidate table with IDs
  - [ ] output JSON schema instructions
- [ ] Implement strict output parser/validator.
- [ ] Implement response repair/retry strategy.

### Guardrails and safety
- [ ] Enforce candidate-ID-only selection.
- [ ] Reject unknown restaurant IDs.
- [ ] Add explanation length bounds.
- [ ] Add content-safety post-filter (if required).

### Reliability and fallback
- [ ] Implement provider timeout.
- [ ] Implement transient retry policy.
- [ ] Implement deterministic fallback recommendation when LLM fails.

### Observability
- [ ] Log prompt version and model version.
- [ ] Log token usage and estimated cost.
- [ ] Log parse failures and retry counts.

### Tests
- [ ] Unit tests for schema parsing.
- [ ] Integration tests with mocked LLM responses (valid/invalid).
- [ ] Hallucination prevention tests (unknown IDs).
- [ ] Groq connectivity smoke test using `.env` API key.

### Phase 3 exit criteria
- [ ] Structured parse success rate meets target.
- [ ] Failure paths produce valid fallback responses.

---

## Phase 4 - API and Orchestration

### Entry criteria
- [ ] Retrieval and LLM layers pass integration tests independently.

### API implementation
- [ ] Implement `POST /recommendations`.
- [ ] Implement `GET /health`.
- [ ] Implement `GET /metrics` (if telemetry enabled).
- [ ] Add request/response validation with typed models.

### Orchestration pipeline
- [ ] Implement stage sequence:
  - [ ] validate
  - [ ] normalize
  - [ ] retrieve
  - [ ] LLM rank/explain
  - [ ] validate and format output
- [ ] Add per-stage latency measurements.
- [ ] Add request ID propagation.

### Reliability controls
- [ ] Add global timeout budget.
- [ ] Add circuit breaker for repeated provider failures.
- [ ] Add graceful degradation mode.

### Tests
- [ ] API contract tests with schema snapshots.
- [ ] End-to-end tests with representative user payloads.
- [ ] Error path tests (bad input, timeout, provider errors).

### Phase 4 exit criteria
- [ ] End-to-end endpoint stable with target success rate.
- [ ] Diagnostics metadata available for every response.

---

## Phase 5 - UI and Interaction Design

### Entry criteria
- [ ] API endpoint stable and documented.

### UI implementation
- [ ] Implement preference input form controls (locality dropdown + numeric amount).
- [ ] Add validation and inline user guidance.
- [ ] Build recommendation card layout with key fields.
- [ ] Display AI explanation and fit score.
- [ ] Add loading, error, and empty states.

### Refinement loop
- [ ] Add quick-refine actions (cheaper/higher rated/nearby).
- [ ] Preserve prior selections between iterations.
- [ ] Display fallback message when constraints were relaxed.

### UX validation
- [ ] Run 5-10 user walkthroughs.
- [ ] Capture friction points and confusion spots.
- [ ] Apply UX fixes and rerun quick validation.

### Phase 5 exit criteria
- [ ] Users can complete flow with minimal confusion.
- [ ] Output is readable and trustable.

---

## Phase 6 - Evaluation and Quality Tuning

### Entry criteria
- [ ] System can run stable end-to-end across typical scenarios.

### Offline evaluation
- [ ] Build benchmark scenario set (50+ cases).
- [ ] Define scoring rubric and automated checks.
- [ ] Track:
  - [ ] constraint adherence
  - [ ] recommendation relevance proxy
  - [ ] explanation quality score

### Online feedback
- [ ] Add thumbs up/down capture.
- [ ] Add reason tags for negative feedback.
- [ ] Store event logs for analysis.

### Tuning loop
- [ ] Tune retrieval weights based on metrics.
- [ ] Tune fallback order and thresholds.
- [ ] Tune prompt wording/examples.
- [ ] Run regression suite before each release.

### Reporting
- [ ] Build KPI dashboard:
  - [ ] p50/p95 latency
  - [ ] success/error rate
  - [ ] parse failure rate
  - [ ] fallback usage
  - [ ] feedback acceptance

### Phase 6 exit criteria
- [ ] At least one measurable KPI improvement over baseline.
- [ ] No critical regression in latency or reliability.

---

## Phase 7 - Production Hardening and Scale

### Entry criteria
- [ ] Baseline quality and reliability targets are met.

### Deployment and release
- [ ] Containerize API service.
- [ ] Set up deployment pipeline (test -> build -> deploy).
- [ ] Configure environments (dev/stage/prod).
- [ ] Configure secrets management.

### Runtime hardening
- [ ] Implement auth/rate limiting.
- [ ] Add quota and budget controls for LLM usage.
- [ ] Add alerting for latency/error/cost anomalies.
- [ ] Add incident runbooks.

### Controlled experimentation
- [ ] Add canary for model/prompt version rollout.
- [ ] Add rollback rules and automation triggers.
- [ ] Add release notes template including KPI delta.

### Phase 7 exit criteria
- [ ] System is merge-ready for production launch.
- [ ] On-call playbook exists and is tested.

---

## Cross-Phase Dependency Checklist

- [ ] No phase starts without prior phase exit criteria.
- [ ] Schema version changes are backward-compatible or migrated.
- [ ] Prompt/model changes always run full regression suite.
- [ ] Data snapshot version is stamped in API metadata.
- [ ] Every deploy includes smoke tests.

---

## Final Go-Live Readiness Checklist

- [ ] p95 latency meets launch target.
- [ ] API success rate meets launch target.
- [ ] Recommendation quality baseline accepted by stakeholders.
- [ ] Observability and alerts are active.
- [ ] Rollback plan validated in staging.
- [ ] Cost-per-request under budget.
- [ ] Security and retention requirements approved.

---

## Information Still Required to Lock Estimates and Owners

- [ ] Expected DAU and peak QPS.
- [ ] Launch geography/city scope.
- [ ] Budget range definitions in currency terms.
- [ ] Preferred UI stack (Streamlit vs React).
- [ ] Preferred cloud/deployment environment.
- [ ] LLM provider/model policy and monthly spend cap.
- [ ] Compliance/log-retention constraints.
- [ ] Team size and role ownership per phase.

