from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetBand:
    min_cost: float
    max_cost: float


BUDGET_BANDS: dict[str, BudgetBand] = {
    "low": BudgetBand(min_cost=0, max_cost=700),
    "medium": BudgetBand(min_cost=701, max_cost=1800),
    "high": BudgetBand(min_cost=1801, max_cost=100000),
}

CUISINE_SYNONYMS: dict[str, str] = {
    "quick bites": "fast food",
    "fast-food": "fast food",
    "italiano": "italian",
    "chineese": "chinese",
}

SCORE_WEIGHTS: dict[str, float] = {
    "rating": 0.45,
    "cuisine_match": 0.30,
    "budget_fit": 0.20,
    "popularity": 0.05,
}

FALLBACK_ORDER: list[str] = [
    "strict",
    "relaxed_budget",
    "relaxed_cuisine",
    "widened_locality",
]
