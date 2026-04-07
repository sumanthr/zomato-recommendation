# Phase 3 Resources (Groq LLM)

## Provider

- LLM provider: **Groq**
- API key source: `.env` via `GROQ_API_KEY`
- Model env key: `LLM_MODEL` (default: `llama-3.1-8b-instant`)

## Source files

- `src/phases/phase_3/client.py` - Groq API client wrapper
- `src/phases/phase_3/prompt_builder.py` - prompt design for ranking/explanations
- `src/phases/phase_3/engine.py` - output validation + fallback handling
- `src/phases/phase_3/pipeline.py` - phase runner tied to Phase 2 candidates

## Tests

- `tests/phase_3/test_phase3_engine.py`
