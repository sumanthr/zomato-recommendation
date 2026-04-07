# Phase 2 Resources (Retrieval, Ranking, Fallbacks)

## Source files

- `src/phases/phase_2/config.py` - budget bands (for categorical budgets), weights, optional fallback order, small cuisine synonym map
- `src/phases/phase_2/normalization.py` - input normalization; locality **exact-then-fuzzy** against inventory
- `src/phases/phase_2/retriever.py` - hard filters, weighted scoring; **numeric budget** = max `avg_cost_for_two`; strict default (no irrelevant backfill)
- `src/phases/phase_2/pipeline.py` - executable runner for phase-specific testing

## Test files

- `tests/phase_2/test_phase2_normalization.py`
- `tests/phase_2/test_phase2_retrieval.py`

## Run

```bash
python -m src.phases.phase_2.pipeline \
  --input-json '{"location":"Bangalore","budget":"medium","cuisine":"Italian","minimum_rating":4.0,"top_k":5}'
```
