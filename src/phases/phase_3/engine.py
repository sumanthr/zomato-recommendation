from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import BaseModel, Field, ValidationError

from src.phases.phase_0.schemas import CandidateRecord, RecommendationItem, UserPreferenceInput
from src.phases.phase_3.client import GroqClient
from src.phases.phase_3.prompt_builder import build_phase3_prompt


class LLMRecommendation(BaseModel):
    restaurant_id: str
    explanation: str = Field(min_length=8)
    fit_score: int = Field(ge=0, le=100)


class LLMRecommendationBundle(BaseModel):
    recommendations: list[LLMRecommendation]


@dataclass
class Phase3Outcome:
    recommendations: list[RecommendationItem]
    llm_used: bool


def validate_llm_output(raw_output: str, allowed_ids: set[str]) -> LLMRecommendationBundle:
    payload = json.loads(raw_output)
    bundle = LLMRecommendationBundle(**payload)
    for item in bundle.recommendations:
        if item.restaurant_id not in allowed_ids:
            raise ValueError(f"Unknown restaurant_id from LLM: {item.restaurant_id}")
    return bundle


def deterministic_fallback(candidates: list[CandidateRecord], top_k: int) -> list[RecommendationItem]:
    top = sorted(candidates, key=lambda c: c.candidate_score, reverse=True)
    results: list[RecommendationItem] = []
    seen: set[tuple[str, str]] = set()
    for c in top:
        dedupe_key = (c.name.strip().lower(), (c.locality or "").strip().lower())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        results.append(
            RecommendationItem(
                restaurant_name=c.name,
                locality=c.locality,
                cuisine=c.cuisines[0].title() if c.cuisines else "Unknown",
                rating=c.rating,
                estimated_cost=c.avg_cost_for_two,
                explanation="Recommended using deterministic ranking fallback.",
                fit_score=max(1, min(100, int(round(c.candidate_score * 100)))),
            )
        )
        if len(results) >= top_k:
            break
    return results


def generate_phase3_recommendations(
    user_input: UserPreferenceInput,
    candidates: list[CandidateRecord],
    client: GroqClient | None = None,
) -> list[RecommendationItem]:
    return generate_phase3_outcome(user_input, candidates, client=client).recommendations


def generate_phase3_outcome(
    user_input: UserPreferenceInput,
    candidates: list[CandidateRecord],
    client: GroqClient | None = None,
) -> Phase3Outcome:
    if not candidates:
        return Phase3Outcome(recommendations=[], llm_used=False)
    if len(candidates) > 30:
        # Avoid oversized prompts; return deterministic ranking for larger result sets.
        return Phase3Outcome(
            recommendations=deterministic_fallback(candidates, user_input.top_k),
            llm_used=False,
        )

    try:
        llm_client = client or GroqClient()
    except Exception:
        return Phase3Outcome(
            recommendations=deterministic_fallback(candidates, user_input.top_k),
            llm_used=False,
        )
    prompt = build_phase3_prompt(user_input, candidates)
    allowed_ids = {c.restaurant_id for c in candidates}
    lookup = {c.restaurant_id: c for c in candidates}

    try:
        raw = llm_client.complete_json(prompt)
        parsed = validate_llm_output(raw, allowed_ids)
    except (ValidationError, ValueError, json.JSONDecodeError, Exception):
        return Phase3Outcome(
            recommendations=deterministic_fallback(candidates, user_input.top_k),
            llm_used=False,
        )

    results: list[RecommendationItem] = []
    selected_keys: set[tuple[str, str]] = set()
    for item in parsed.recommendations[: user_input.top_k]:
        c = lookup[item.restaurant_id]
        dedupe_key = (c.name.strip().lower(), (c.locality or "").strip().lower())
        if dedupe_key in selected_keys:
            continue
        selected_keys.add(dedupe_key)
        results.append(
            RecommendationItem(
                restaurant_name=c.name,
                locality=c.locality,
                cuisine=c.cuisines[0].title() if c.cuisines else "Unknown",
                rating=c.rating,
                estimated_cost=c.avg_cost_for_two,
                explanation=item.explanation,
                fit_score=item.fit_score,
            )
        )

    if len(results) < user_input.top_k:
        fallback_candidates = deterministic_fallback(candidates, user_input.top_k)
        for fb in fallback_candidates:
            dedupe_key = (
                fb.restaurant_name.strip().lower(),
                (fb.locality or "").strip().lower(),
            )
            if dedupe_key in selected_keys:
                continue
            results.append(fb)
            selected_keys.add(dedupe_key)
            if len(results) >= user_input.top_k:
                break
    return Phase3Outcome(recommendations=results, llm_used=True)
