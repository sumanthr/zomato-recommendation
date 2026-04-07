from pathlib import Path

import pandas as pd

from src.phases.phase_0.schemas import UserPreferenceInput
from src.phases.phase_2.retriever import retrieve_candidates


def _write_curated_fixture(path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "restaurant_id": "1",
                "name": "Pasta Point",
                "location_city": "Bangalore",
                "locality": "Indiranagar",
                "cuisines": ["italian", "continental"],
                "avg_cost_for_two": 1200.0,
                "rating": 4.3,
            },
            {
                "restaurant_id": "2",
                "name": "Spice Hub",
                "location_city": "Bangalore",
                "locality": "Koramangala",
                "cuisines": ["indian"],
                "avg_cost_for_two": 900.0,
                "rating": 4.4,
            },
            {
                "restaurant_id": "3",
                "name": "Luxury Bites",
                "location_city": "Delhi",
                "locality": "CP",
                "cuisines": ["italian"],
                "avg_cost_for_two": 2800.0,
                "rating": 4.6,
            },
        ]
    )
    df.to_parquet(path, index=False)


def test_retrieval_returns_ranked_candidates(tmp_path: Path) -> None:
    curated = tmp_path / "restaurants.parquet"
    _write_curated_fixture(curated)

    user_input = UserPreferenceInput(
        location="Indiranagar",
        budget="medium",
        cuisine="Italian",
        minimum_rating=4.0,
        top_k=5,
    )
    result = retrieve_candidates(user_input, curated_path=str(curated))
    assert len(result.candidates) >= 1
    assert result.candidates[0].name == "Pasta Point"
    assert result.fallback_tier in {"strict", "relaxed_budget", "relaxed_cuisine", "widened_locality"}


def test_retrieval_applies_fallback_when_strict_empty(tmp_path: Path) -> None:
    curated = tmp_path / "restaurants.parquet"
    _write_curated_fixture(curated)

    user_input = UserPreferenceInput(
        location="Indiranagar",
        budget="low",
        cuisine="Chinese",
        minimum_rating=4.0,
        top_k=5,
    )
    result = retrieve_candidates(user_input, curated_path=str(curated))
    assert result.fallback_tier in {
        "relaxed_budget",
        "relaxed_cuisine",
        "widened_locality",
        "no_candidates",
    }
