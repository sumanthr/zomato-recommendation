# Phase 4 Resources (API + Orchestration)

## Source files

- `src/phases/phase_4/orchestrator.py` - validate/normalize/retrieve/LLM orchestration bridge
- `src/phases/phase_4/api.py` - FastAPI routes (`/health`, `/metrics`, `/recommendations`)
- `src/phases/phase_4/metrics.py` - request success/failure counters

## Run API

```bash
uvicorn src.phases.phase_4.api:app --reload
```
