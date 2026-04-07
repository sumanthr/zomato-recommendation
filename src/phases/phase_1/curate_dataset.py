from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.phases.phase_1.normalization import (
    clamp_rating,
    normalize_text,
    parse_cuisines,
    parse_float,
)
from src.phases.phase_1.quality import generate_quality_report


CANONICAL_COLUMNS = [
    "restaurant_id",
    "name",
    "location_city",
    "locality",
    "cuisines",
    "avg_cost_for_two",
    "rating",
]


def _resolve_value(row: pd.Series, candidates: list[str], default: Any = None) -> Any:
    for col in candidates:
        if col in row and pd.notna(row[col]):
            return row[col]
    return default


def curate_dataset(
    input_path: str = "data/raw/zomato_raw.parquet", output_dir: str = "data/processed"
) -> tuple[Path, Path, Path]:
    in_path = Path(input_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file missing: {in_path}")

    out_dir = Path(output_dir)
    report_dir = Path("data/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    raw_df = pd.read_parquet(in_path)

    curated_rows: list[dict[str, Any]] = []
    for idx, row in raw_df.iterrows():
        name = _resolve_value(
            row,
            ["Restaurant Name", "name", "restaurant_name"],
            "",
        )
        city = _resolve_value(
            row,
            ["City", "city", "location_city", "listed_in(city)"],
            "",
        )
        locality = _resolve_value(
            row,
            ["Locality", "locality", "location"],
            "",
        )
        cuisines_raw = _resolve_value(
            row,
            ["Cuisines", "cuisines"],
            "",
        )
        rating_raw = _resolve_value(
            row,
            ["Aggregate rating", "rating", "rate"],
            None,
        )
        cost_raw = _resolve_value(
            row,
            ["Average Cost for two", "avg_cost_for_two", "approx_cost(for two people)"],
            None,
        )
        rest_id = _resolve_value(
            row, ["Restaurant ID", "restaurant_id", "id"], f"zomato-{idx}"
        )

        parsed_rating = clamp_rating(parse_float(rating_raw))
        parsed_cost = parse_float(cost_raw)

        curated_rows.append(
            {
                "restaurant_id": str(rest_id),
                "name": normalize_text(name).title(),
                "location_city": normalize_text(city).title(),
                "locality": normalize_text(locality).title() if locality else None,
                "cuisines": parse_cuisines(cuisines_raw),
                "avg_cost_for_two": parsed_cost,
                "rating": parsed_rating,
            }
        )

    curated_df = pd.DataFrame(curated_rows)[CANONICAL_COLUMNS]
    curated_df = curated_df[curated_df["name"].str.len() > 0]
    curated_df = curated_df[curated_df["location_city"].str.len() > 0]
    curated_df = curated_df.drop_duplicates(subset=["name", "location_city", "locality"])
    curated_df = curated_df.reset_index(drop=True)

    parquet_path = out_dir / "restaurants.parquet"
    jsonl_path = out_dir / "restaurants_serving.jsonl"
    quality_path = report_dir / "data_quality.json"

    curated_df.to_parquet(parquet_path, index=False)
    curated_df.to_json(jsonl_path, orient="records", lines=True, force_ascii=True)

    quality = generate_quality_report(curated_df)
    quality_path.write_text(json.dumps(quality.to_dict(), indent=2), encoding="utf-8")

    return parquet_path, jsonl_path, quality_path


if __name__ == "__main__":
    outputs = curate_dataset()
    print("Curated artifacts generated:")
    for artifact in outputs:
        print(f"- {artifact}")
