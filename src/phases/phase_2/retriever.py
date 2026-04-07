from __future__ import annotations

import time
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from src.phases.phase_0.schemas import CandidateRecord, UserPreferenceInput
from src.phases.phase_2.config import BUDGET_BANDS, SCORE_WEIGHTS
from src.phases.phase_2.models import RetrievalResult
from src.phases.phase_2.normalization import canonicalize_cuisine, normalize_user_input


def _load_curated_data(curated_path: str) -> pd.DataFrame:
    path = Path(curated_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Curated dataset missing: {curated_path}. Run Phase 1 pipeline first."
        )
    return pd.read_parquet(path)


def _parse_cuisine_list(value: object) -> list[str]:
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return [canonicalize_cuisine(str(item).strip().lower()) for item in value]
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        parts = [p.strip().strip("'").strip('"') for p in raw.split(",")]
        return [canonicalize_cuisine(p.lower()) for p in parts if p]
    return []


def _apply_filters(
    df: pd.DataFrame,
    *,
    locality: str,
    min_rating: float,
    budget_min: float,
    budget_max: float,
    target_cuisine: str,
    tier: str,
) -> pd.DataFrame:
    filtered = df.copy()

    if tier != "widened_locality":
        filtered = filtered[filtered["locality"].fillna("").str.lower() == locality.lower()]

    filtered = filtered[filtered["rating"].fillna(0.0) >= min_rating]

    if tier in {"strict", "relaxed_cuisine", "widened_locality"}:
        filtered = filtered[
            filtered["avg_cost_for_two"].fillna(-1).between(budget_min, budget_max)
        ]
    if tier == "relaxed_budget":
        relaxed_min = max(0, budget_min * 0.75)
        relaxed_max = budget_max * 1.25
        filtered = filtered[
            filtered["avg_cost_for_two"].fillna(-1).between(relaxed_min, relaxed_max)
        ]

    if tier in {"strict", "relaxed_budget"}:
        filtered = filtered[
            filtered["cuisines"].apply(
                lambda cuisines: target_cuisine in _parse_cuisine_list(cuisines)
            )
        ]
    return filtered


def _score_candidates(df: pd.DataFrame, *, target_cuisine: str, budget_min: float, budget_max: float) -> pd.DataFrame:
    if df.empty:
        return df

    midpoint = (budget_min + budget_max) / 2
    denom = max(midpoint, 1.0)

    def cuisine_match_score(cuisines: object) -> float:
        values = _parse_cuisine_list(cuisines)
        return 1.0 if target_cuisine in values else 0.3

    def budget_fit_score(cost: object) -> float:
        if cost is None or pd.isna(cost):
            return 0.3
        distance = abs(float(cost) - midpoint) / denom
        return max(0.0, min(1.0, 1.0 - distance))

    scored = df.copy()
    scored["rating_component"] = scored["rating"].fillna(0.0) / 5.0
    scored["cuisine_component"] = scored["cuisines"].apply(cuisine_match_score)
    scored["budget_component"] = scored["avg_cost_for_two"].apply(budget_fit_score)
    scored["popularity_component"] = scored["rating_component"]

    scored["candidate_score"] = (
        SCORE_WEIGHTS["rating"] * scored["rating_component"]
        + SCORE_WEIGHTS["cuisine_match"] * scored["cuisine_component"]
        + SCORE_WEIGHTS["budget_fit"] * scored["budget_component"]
        + SCORE_WEIGHTS["popularity"] * scored["popularity_component"]
    )
    return scored.sort_values("candidate_score", ascending=False)


def retrieve_candidates(
    user_input: UserPreferenceInput, curated_path: str = "data/processed/restaurants.parquet"
) -> RetrievalResult:
    start = time.perf_counter()
    df = _load_curated_data(curated_path)
    localities = [str(c).strip().lower() for c in df["locality"].dropna().unique()]
    normalized = normalize_user_input(user_input, localities)

    if isinstance(user_input.budget, (int, float)):
        budget_min = 0.0
        budget_max = float(user_input.budget)
    else:
        budget_band = BUDGET_BANDS[normalized.budget]
        budget_min = budget_band.min_cost
        budget_max = budget_band.max_cost
    chosen_tier = "strict"
    fallback_reason = "strict constraints satisfied"
    selected = _apply_filters(
        df,
        locality=normalized.location_city,
        min_rating=normalized.minimum_rating,
        budget_min=budget_min,
        budget_max=budget_max,
        target_cuisine=normalized.cuisine,
        tier="strict",
    )

    if selected.empty:
        chosen_tier = "no_candidates"
        fallback_reason = "no candidates matching strict filters"

    scored = _score_candidates(
        selected,
        target_cuisine=normalized.cuisine,
        budget_min=budget_min,
        budget_max=budget_max,
    ).head(normalized.top_k)

    candidates: list[CandidateRecord] = []
    for _, row in scored.iterrows():
        candidates.append(
            CandidateRecord(
                restaurant_id=str(row["restaurant_id"]),
                name=str(row["name"]),
                locality=(str(row["locality"]) if pd.notna(row.get("locality")) else None),
                cuisines=_parse_cuisine_list(row["cuisines"]),
                rating=float(row["rating"]) if pd.notna(row["rating"]) else None,
                avg_cost_for_two=(
                    float(row["avg_cost_for_two"])
                    if pd.notna(row["avg_cost_for_two"])
                    else None
                ),
                candidate_score=round(float(row["candidate_score"]), 4),
                score_breakdown={
                    "rating": round(float(row["rating_component"]), 4),
                    "cuisine_match": round(float(row["cuisine_component"]), 4),
                    "budget_fit": round(float(row["budget_component"]), 4),
                    "popularity": round(float(row["popularity_component"]), 4),
                },
            )
        )

    normalized_input = UserPreferenceInput(
        location=normalized.location_city,
        budget=normalized.budget,
        cuisine=normalized.cuisine,
        minimum_rating=normalized.minimum_rating,
        additional_preferences=normalized.additional_preferences,
        top_k=normalized.top_k,
    )

    end = time.perf_counter()
    return RetrievalResult(
        normalized_input=normalized_input,
        normalized_context=normalized,
        candidates=candidates,
        fallback_tier=chosen_tier,
        fallback_reason=fallback_reason,
        stage_latency_ms={"retrieval": int((end - start) * 1000)},
    )


def list_localities(
    curated_path: str = "data/processed/restaurants.parquet", limit: int = 200
) -> list[str]:
    df = _load_curated_data(curated_path)
    values = (
        df["locality"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
        .head(limit)
        .tolist()
    )
    return values


def dataset_summary(curated_path: str = "data/processed/restaurants.parquet") -> dict[str, int]:
    df = _load_curated_data(curated_path)
    locality_count = (
        df["locality"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()
        if "locality" in df.columns
        else 0
    )
    city_count = (
        df["location_city"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()
        if "location_city" in df.columns
        else 0
    )
    return {
        "restaurant_count": int(len(df)),
        "locality_count": int(locality_count),
        "city_count": int(city_count),
    }
