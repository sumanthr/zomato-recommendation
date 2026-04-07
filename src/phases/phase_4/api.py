from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.phases.phase_0.schemas import RecommendationResponse, UserPreferenceInput
from src.phases.phase_2.retriever import dataset_summary, list_localities
from src.phases.phase_4.metrics import MetricsStore
from src.phases.phase_4.orchestrator import run_recommendation_orchestration

app = FastAPI(title="Zomato Recommendation API", version="phase4")
metrics_store = MetricsStore()
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
env_origins = [
    item.strip()
    for item in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if item.strip()
]
allowed_origins = sorted(set(default_origins + env_origins))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> dict[str, int]:
    return metrics_store.snapshot()


@app.get("/localities")
def localities(limit: int = 200) -> dict[str, list[str]]:
    curated_path = os.getenv("CURATED_DATA_PATH", "data/processed/restaurants.parquet")
    return {"localities": list_localities(curated_path=curated_path, limit=limit)}


@app.get("/dataset-summary")
def summary() -> dict[str, int]:
    curated_path = os.getenv("CURATED_DATA_PATH", "data/processed/restaurants.parquet")
    return dataset_summary(curated_path=curated_path)


@app.post("/recommendations", response_model=RecommendationResponse)
def recommendations(payload: UserPreferenceInput) -> RecommendationResponse:
    try:
        curated_path = os.getenv("CURATED_DATA_PATH", "data/processed/restaurants.parquet")
        result = run_recommendation_orchestration(payload, curated_path=curated_path)
        metrics_store.mark_success()
        return result
    except Exception as exc:
        metrics_store.mark_failure()
        raise HTTPException(status_code=500, detail=f"recommendation_error: {exc}") from exc
