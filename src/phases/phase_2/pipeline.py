from __future__ import annotations

import argparse
import json

from src.phases.phase_0.schemas import UserPreferenceInput
from src.phases.phase_2.retriever import retrieve_candidates


def run_phase2(input_json: str, curated_path: str) -> dict:
    payload = json.loads(input_json)
    user_input = UserPreferenceInput(**payload)
    result = retrieve_candidates(user_input, curated_path=curated_path)
    return {
        "normalized_input": result.normalized_input.model_dump(),
        "fallback_tier": result.fallback_tier,
        "fallback_reason": result.fallback_reason,
        "normalization_confidence": result.normalized_context.normalization_confidence,
        "stage_latency_ms": result.stage_latency_ms,
        "candidates": [candidate.model_dump() for candidate in result.candidates],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 2 candidate retrieval.")
    parser.add_argument("--input-json", required=True, help="User preferences as JSON string")
    parser.add_argument(
        "--curated-path",
        default="data/processed/restaurants.parquet",
        help="Path to phase 1 curated parquet file",
    )
    args = parser.parse_args()
    output = run_phase2(args.input_json, args.curated_path)
    print(json.dumps(output, indent=2))
