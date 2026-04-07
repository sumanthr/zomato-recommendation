# Zomato Recommendation

Phase 0 to Phase 7 implementation scaffold for an AI-powered restaurant recommendation service.

## Tech choices

- Backend/API: Python + FastAPI
- Data processing: Pandas + Hugging Face Datasets
- Frontend stack (selected): ReactJS (implementation starts in later UI phase)
- LLM provider for Phase 3: Groq (`GROQ_API_KEY` in `.env`)

## Project structure

- `src/phases/phase_0/` - contracts, schema definitions, API scaffold
- `src/phases/phase_1/` - data ingestion, curation, normalization, quality checks
- `src/phases/phase_2/` - input normalization, retrieval, ranking, fallback logic
- `src/phases/phase_3/` - Groq LLM ranking, explanation generation, and validation
- `src/phases/phase_4/` - API orchestration (`/recommendations`, `/metrics`, `/health`)
- `src/phases/phase_5/` - React frontend experience layer
- `src/phases/phase_6/` - evaluation suite and feedback capture
- `src/phases/phase_7/` - deployment and hardening assets
- `docs/contracts/` - frozen contract examples for Phase 0
- `docs/phases/` - phase-specific docs and run instructions
- `tests/` - unit, integration, and e2e test folders

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add Groq credentials in `.env`:

```bash
GROQ_API_KEY=<your_groq_api_key>
LLM_MODEL=llama-3.1-8b-instant
```

## Run tests (Phase 0 quality gate)

```bash
pytest
```

Run phase-specific tests:

```bash
pytest tests/phase_2 -q
```

```bash
pytest tests/phase_3 -q
```

```bash
pytest tests/phase_4 -q
```

```bash
pytest tests/phase_6 tests/phase_7 -q
```

## Run Phase 1 pipeline

This downloads the dataset from Hugging Face and produces curated artifacts.

```bash
python -m src.phases.phase_1.pipeline
```

If Hugging Face is blocked in your network, provide a local parquet file path:

```bash
export ZOMATO_LOCAL_RAW_PATH=/absolute/path/to/zomato_raw.parquet
python -m src.phases.phase_1.pipeline
```

## Expected artifacts after Phase 1 run

- `data/raw/zomato_raw.parquet`
- `data/raw/zomato_raw_metadata.json`
- `data/processed/restaurants.parquet`
- `data/processed/restaurants_serving.jsonl`
- `data/reports/data_quality.json`

## API scaffold check

```bash
uvicorn src.phases.phase_0.api:app --reload
```

Health endpoint:

- `GET /health`

## Run Phase 2 retrieval pipeline

```bash
python -m src.phases.phase_2.pipeline \
  --input-json '{"location":"Bangalore","budget":"medium","cuisine":"Italian","minimum_rating":4.0,"top_k":5}'
```

## Run Phase 3 LLM recommendation pipeline

```bash
python -m src.phases.phase_3.pipeline \
  --input-json '{"location":"Bangalore","budget":"medium","cuisine":"Italian","minimum_rating":4.0,"top_k":5}'
```

## Run Phase 4 API (end-to-end orchestration)

```bash
uvicorn src.phases.phase_4.api:app --reload
```

## Run Phase 5 frontend (React)

```bash
cd src/phases/phase_5/frontend
npm install
npm run dev
```

### One-command start/stop (backend + frontend)

```bash
./scripts/dev-up.sh
```

```bash
./scripts/dev-down.sh
```

These scripts also force-stop stale processes on ports `8001` and `5174` to avoid old code serving requests.
Sample data bootstrap is only used when curated parquet is missing. Set `FORCE_SAMPLE_DATA=true` to force sample refresh.

## Run Phase 6 evaluation

```bash
python -m src.phases.phase_6.evaluator
```

## Run Phase 7 local bootstrap

```bash
python -m src.phases.phase_7.bootstrap_sample_data
```