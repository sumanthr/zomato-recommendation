from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd


@dataclass
class DataQualityReport:
    row_count: int
    null_rate_name: float
    null_rate_location_city: float
    null_rate_cuisines: float
    invalid_rating_rate: float
    invalid_cost_rate: float
    duplicate_rate: float
    checks_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_quality_report(df: pd.DataFrame) -> DataQualityReport:
    total = max(len(df), 1)

    null_name = float(df["name"].isna().mean()) if "name" in df.columns else 1.0
    null_city = (
        float(df["location_city"].isna().mean()) if "location_city" in df.columns else 1.0
    )
    null_cuisines = (
        float(df["cuisines"].isna().mean()) if "cuisines" in df.columns else 1.0
    )

    if "rating" in df.columns:
        invalid_rating = ((df["rating"] < 0) | (df["rating"] > 5)).fillna(False).mean()
    else:
        invalid_rating = 1.0

    if "avg_cost_for_two" in df.columns:
        invalid_cost = (df["avg_cost_for_two"] < 0).fillna(False).mean()
    else:
        invalid_cost = 1.0

    duplicate_rate = (
        df.duplicated(subset=["name", "location_city", "locality"]).sum() / total
        if {"name", "location_city", "locality"}.issubset(df.columns)
        else 1.0
    )

    checks_passed = all(
        [
            null_name < 0.10,
            null_city < 0.10,
            null_cuisines < 0.20,
            float(invalid_rating) < 0.05,
            float(invalid_cost) < 0.05,
            duplicate_rate < 0.20,
        ]
    )

    return DataQualityReport(
        row_count=len(df),
        null_rate_name=float(null_name),
        null_rate_location_city=float(null_city),
        null_rate_cuisines=float(null_cuisines),
        invalid_rating_rate=float(invalid_rating),
        invalid_cost_rate=float(invalid_cost),
        duplicate_rate=float(duplicate_rate),
        checks_passed=checks_passed,
    )
