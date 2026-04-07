from __future__ import annotations

from pathlib import Path

import pandas as pd


def _build_sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"restaurant_id": "sample-1", "name": "Pasta Point", "location_city": "Bangalore", "locality": "Indiranagar", "cuisines": ["italian", "continental"], "avg_cost_for_two": 1200.0, "rating": 4.4},
            {"restaurant_id": "sample-2", "name": "Spice Hub", "location_city": "Bangalore", "locality": "Koramangala", "cuisines": ["indian", "north indian"], "avg_cost_for_two": 900.0, "rating": 4.2},
            {"restaurant_id": "sample-3", "name": "Dragon Bowl", "location_city": "Delhi", "locality": "Connaught Place", "cuisines": ["chinese"], "avg_cost_for_two": 800.0, "rating": 4.1},
            {"restaurant_id": "sample-4", "name": "Bistro 24", "location_city": "Bangalore", "locality": "HSR Layout", "cuisines": ["italian", "mexican"], "avg_cost_for_two": 1600.0, "rating": 4.5},
            {"restaurant_id": "sample-5", "name": "Curry House", "location_city": "Delhi", "locality": "Saket", "cuisines": ["indian"], "avg_cost_for_two": 700.0, "rating": 4.0},
            {"restaurant_id": "sample-6", "name": "Noodle Spot", "location_city": "Delhi", "locality": "Hauz Khas", "cuisines": ["chinese", "thai"], "avg_cost_for_two": 1100.0, "rating": 4.3},
            {"restaurant_id": "sample-7", "name": "Urban Tawa", "location_city": "Bangalore", "locality": "Whitefield", "cuisines": ["indian", "kebab"], "avg_cost_for_two": 1300.0, "rating": 4.1},
            {"restaurant_id": "sample-8", "name": "Sushi Dock", "location_city": "Bangalore", "locality": "Jayanagar", "cuisines": ["japanese"], "avg_cost_for_two": 2200.0, "rating": 4.6},
            {"restaurant_id": "sample-9", "name": "Budget Bites", "location_city": "Bangalore", "locality": "Marathahalli", "cuisines": ["fast food"], "avg_cost_for_two": 450.0, "rating": 3.9},
            {"restaurant_id": "sample-10", "name": "Taco Trail", "location_city": "Delhi", "locality": "Karol Bagh", "cuisines": ["mexican"], "avg_cost_for_two": 950.0, "rating": 4.0},
            {"restaurant_id": "sample-11", "name": "Royal Feast", "location_city": "Delhi", "locality": "Dwarka", "cuisines": ["north indian"], "avg_cost_for_two": 1800.0, "rating": 4.4},
            {"restaurant_id": "sample-12", "name": "Cafe Verde", "location_city": "Bangalore", "locality": "BTM Layout", "cuisines": ["continental", "italian"], "avg_cost_for_two": 1000.0, "rating": 4.2},
        ]
    )


def ensure_sample_curated_dataset(
    output_path: str = "data/processed/restaurants.parquet",
) -> Path:
    path = Path(output_path)
    if path.exists():
        existing = pd.read_parquet(path)
        locality_count = (
            existing["locality"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()
            if "locality" in existing.columns
            else 0
        )
        if len(existing) >= 10 and locality_count >= 5:
            return path

    path.parent.mkdir(parents=True, exist_ok=True)
    sample = _build_sample_frame()
    sample.to_parquet(path, index=False)
    return path


if __name__ == "__main__":
    created = ensure_sample_curated_dataset()
    print(f"Sample curated dataset ready at: {created}")
