from __future__ import annotations

import json

from src.phases.phase_0.schemas import CandidateRecord, UserPreferenceInput


def build_phase3_prompt(
    user_input: UserPreferenceInput, candidates: list[CandidateRecord]
) -> str:
    candidate_payload = [
        {
            "restaurant_id": c.restaurant_id,
            "name": c.name,
            "cuisines": c.cuisines,
            "rating": c.rating,
            "avg_cost_for_two": c.avg_cost_for_two,
            "candidate_score": c.candidate_score,
        }
        for c in candidates
    ]

    return (
        "You are a restaurant recommendation ranker.\n"
        "Only choose from the exact restaurant_id values provided.\n"
        "Return STRICT JSON with this schema:\n"
        '{ "recommendations": [ { "restaurant_id": "...", "explanation": "...", "fit_score": 0-100 } ] }\n'
        f"Return at most {user_input.top_k} recommendations.\n"
        "User preferences:\n"
        f"{json.dumps(user_input.model_dump(), ensure_ascii=True)}\n"
        "Candidate set:\n"
        f"{json.dumps(candidate_payload, ensure_ascii=True)}"
    )
