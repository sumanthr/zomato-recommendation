import pytest
from pydantic import ValidationError

from src.phases.phase_0.schemas import UserPreferenceInput


def test_budget_validation_accepts_known_values() -> None:
    payload = UserPreferenceInput(
        location="Bangalore", budget="medium", cuisine="Italian", minimum_rating=4.0
    )
    assert payload.budget == "medium"


def test_budget_validation_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        UserPreferenceInput(
            location="Bangalore",
            budget="premium",
            cuisine="Italian",
            minimum_rating=4.0,
        )
