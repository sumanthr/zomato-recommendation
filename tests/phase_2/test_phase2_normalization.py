from src.phases.phase_0.schemas import UserPreferenceInput
from src.phases.phase_2.normalization import canonicalize_cuisine, normalize_user_input


def test_canonicalize_cuisine_synonym() -> None:
    assert canonicalize_cuisine("quick bites") == "fast food"


def test_normalization_resolves_city_and_confidence() -> None:
    input_payload = UserPreferenceInput(
        location="bengaluru",
        budget="medium",
        cuisine="Italian",
        minimum_rating=4.0,
        top_k=5,
    )
    normalized = normalize_user_input(input_payload, ["bangalore", "delhi"])
    assert normalized.location_city == "Bangalore"
    assert 0.0 <= normalized.normalization_confidence <= 1.0
