from pathlib import Path

from src.phases.phase_7.bootstrap_sample_data import ensure_sample_curated_dataset


def test_phase7_bootstrap_creates_dataset(tmp_path: Path) -> None:
    target = tmp_path / "processed" / "restaurants.parquet"
    created = ensure_sample_curated_dataset(output_path=str(target))
    assert created.exists()
