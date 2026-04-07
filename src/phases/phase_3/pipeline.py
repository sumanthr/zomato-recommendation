from __future__ import annotations

import argparse
import json

from src.phases.phase_0.schemas import UserPreferenceInput
from src.phases.phase_2.retriever import retrieve_candidates
from src.phases.phase_3.engine import generate_phase3_recommendations


def run_phase3(input_json: str, curated_path: str) -> dict:
    payload = UserPreferenceInput(**json.loads(input_json))
    retrieval = retrieve_candidates(payload, curated_path=curated_path)
    recommendations = generate_phase3_recommendations(payload, retrieval.candidates)
    return {
        "normalized_input": retrieval.normalized_input.model_dump(),
        "fallback_tier": retrieval.fallback_tier,
        "candidate_count": len(retrieval.candidates),
        "recommendations": [item.model_dump() for item in recommendations],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 3 Groq recommendation engine.")
    parser.add_argument("--input-json", required=True, help="User preferences as JSON string")
    parser.add_argument(
        "--curated-path",
        default="data/processed/restaurants.parquet",
        help="Path to curated parquet generated in phase 1",
    )
    args = parser.parse_args()
    output = run_phase3(args.input_json, args.curated_path)
    print(json.dumps(output, indent=2))
