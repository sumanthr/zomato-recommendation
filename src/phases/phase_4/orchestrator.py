from __future__ import annotations

import os
from datetime import datetime, timezone

from src.phases.phase_0.schemas import (
    RecommendationMetadata,
    RecommendationResponse,
    UserPreferenceInput,
)
from src.phases.phase_2.retriever import retrieve_candidates
from src.phases.phase_3.config import DEFAULT_PROMPT_VERSION
from src.phases.phase_3.engine import generate_phase3_recommendations


def run_recommendation_orchestration(
    user_input: UserPreferenceInput,
    curated_path: str = "data/processed/restaurants.parquet",
) -> RecommendationResponse:
    retrieval = retrieve_candidates(user_input, curated_path=curated_path)
    recommendations = generate_phase3_recommendations(
        retrieval.normalized_input, retrieval.candidates
    )

    metadata = RecommendationMetadata(
        prompt_version=DEFAULT_PROMPT_VERSION,
        model_version=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        data_version=datetime.now(timezone.utc).date().isoformat(),
        fallback_tier=retrieval.fallback_tier,
    )
    return RecommendationResponse(
        normalized_input=retrieval.normalized_input,
        recommendations=recommendations,
        metadata=metadata,
    )
