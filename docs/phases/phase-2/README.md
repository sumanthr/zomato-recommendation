# Phase 2 Resources (Retrieval, Ranking, Fallbacks)

## Source files

- `src/phases/phase_2/config.py` - budget bands, weights, fallback order, cuisine synonyms
- `src/phases/phase_2/normalization.py` - input normalization and fuzzy location matching
- `src/phases/phase_2/retriever.py` - hard filters, weighted scoring, fallback tiers
- `src/phases/phase_2/pipeline.py` - executable runner for phase-specific testing

## Test files

- `tests/phase_2/test_phase2_normalization.py`
- `tests/phase_2/test_phase2_retrieval.py`

## Run

```bash
python -m src.phases.phase_2.pipeline \
  --input-json '{"location":"Bangalore","budget":"medium","cuisine":"Italian","minimum_rating":4.0,"top_k":5}'
```
