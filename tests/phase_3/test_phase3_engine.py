import os

import pytest
from dotenv import load_dotenv

from src.phases.phase_0.schemas import CandidateRecord, UserPreferenceInput
from src.phases.phase_3.client import GroqClient
from src.phases.phase_3.engine import (
    deterministic_fallback,
    generate_phase3_recommendations,
    validate_llm_output,
)
from src.phases.phase_3.prompt_builder import build_phase3_prompt

load_dotenv()


class FakeClient:
    def __init__(self, response: str) -> None:
        self._response = response

    def complete_json(self, prompt: str) -> str:
        return self._response


def _sample_candidates() -> list[CandidateRecord]:
    return [
        CandidateRecord(
            restaurant_id="r1",
            name="Pasta Point",
            cuisines=["italian"],
            rating=4.4,
            avg_cost_for_two=1300,
            candidate_score=0.92,
            score_breakdown={},
        ),
        CandidateRecord(
            restaurant_id="r2",
            name="Spice Hub",
            cuisines=["indian"],
            rating=4.2,
            avg_cost_for_two=900,
            candidate_score=0.78,
            score_breakdown={},
        ),
    ]


def test_prompt_contains_candidate_ids() -> None:
    payload = UserPreferenceInput(
        location="Bangalore", budget="medium", cuisine="Italian", minimum_rating=4.0, top_k=2
    )
    prompt = build_phase3_prompt(payload, _sample_candidates())
    assert "r1" in prompt and "r2" in prompt


def test_validate_llm_output_rejects_unknown_id() -> None:
    bad_json = '{"recommendations":[{"restaurant_id":"unknown","explanation":"good fit","fit_score":87}]}'
    with pytest.raises(ValueError):
        validate_llm_output(bad_json, {"r1", "r2"})


def test_generate_uses_fallback_when_malformed_json() -> None:
    payload = UserPreferenceInput(
        location="Bangalore", budget="medium", cuisine="Italian", minimum_rating=4.0, top_k=2
    )
    recs = generate_phase3_recommendations(
        payload, _sample_candidates(), client=FakeClient("not-json")
    )
    assert recs[0].restaurant_name == "Pasta Point"
    assert "fallback" in recs[0].explanation.lower()


def test_groq_connectivity_smoke() -> None:
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set; skipping live connectivity test")
    client = GroqClient()
    assert client.connectivity_smoke_test() is True
