from __future__ import annotations

from typing import Iterable

from rapidfuzz import process

from src.phases.phase_0.schemas import UserPreferenceInput
from src.phases.phase_2.config import BUDGET_BANDS, CUISINE_SYNONYMS
from src.phases.phase_2.models import NormalizedPreference


def canonicalize_cuisine(cuisine: str) -> str:
    value = cuisine.strip().lower()
    return CUISINE_SYNONYMS.get(value, value)


def resolve_budget(budget: float | str) -> str:
    if isinstance(budget, (int, float)):
        amount = float(budget)
        if amount <= BUDGET_BANDS["low"].max_cost:
            return "low"
        if amount <= BUDGET_BANDS["medium"].max_cost:
            return "medium"
        return "high"

    value = str(budget).strip().lower()
    if value in BUDGET_BANDS:
        return value
    try:
        numeric = float(value)
        return resolve_budget(numeric)
    except ValueError:
        return "medium"


def fuzzy_match_location(raw_location: str, available_localities: Iterable[str]) -> tuple[str, float]:
    locality_choices = [loc for loc in available_localities if loc]
    if not locality_choices:
        return raw_location.strip().title(), 0.0
    normalized_raw = raw_location.strip().lower()
    for locality in locality_choices:
        if str(locality).strip().lower() == normalized_raw:
            return str(locality).title(), 1.0

    best = process.extractOne(normalized_raw, locality_choices, score_cutoff=60)
    if best is None:
        return raw_location.strip().title(), 0.40

    locality, score, _ = best
    confidence = round(float(score) / 100.0, 2)
    return str(locality).title(), confidence


def normalize_user_input(
    user_input: UserPreferenceInput, available_localities: Iterable[str]
) -> NormalizedPreference:
    budget = resolve_budget(user_input.budget)
    cuisine = canonicalize_cuisine(user_input.cuisine)
    locality, location_conf = fuzzy_match_location(user_input.location, available_localities)

    confidence_parts = [
        1.0 if budget == resolve_budget(user_input.budget) else 0.8,
        1.0 if cuisine == user_input.cuisine.strip().lower() else 0.8,
        location_conf,
    ]
    normalization_confidence = round(sum(confidence_parts) / len(confidence_parts), 2)

    return NormalizedPreference(
        location_city=locality,
        location_match_confidence=location_conf,
        budget=budget,
        cuisine=cuisine,
        minimum_rating=user_input.minimum_rating,
        additional_preferences=user_input.additional_preferences,
        top_k=user_input.top_k,
        normalization_confidence=normalization_confidence,
    )
