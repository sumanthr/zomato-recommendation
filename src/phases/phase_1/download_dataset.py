from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import shutil

from datasets import load_dataset

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"


def download_raw_dataset(
    dataset_id: str = DATASET_ID,
    split: str = "train",
    output_dir: str = "data/raw",
    local_fallback_path: str | None = None,
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    raw_file = output_path / "zomato_raw.parquet"
    metadata_path = output_path / "zomato_raw_metadata.json"

    if local_fallback_path:
        fallback = Path(local_fallback_path)
        if not fallback.exists():
            raise FileNotFoundError(f"Fallback dataset file not found: {fallback}")
        shutil.copy(fallback, raw_file)
        metadata = {
            "dataset_id": dataset_id,
            "split": split,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "row_count": "unknown_local_fallback",
            "columns": [],
            "source_mode": "local_fallback",
            "fallback_path": str(fallback),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return raw_file

    try:
        dataset = load_dataset(dataset_id, split=split)
    except Exception as exc:
        raise RuntimeError(
            "Failed to download Hugging Face dataset. "
            "If your network blocks Hugging Face, pass a local parquet file via "
            "'local_fallback_path' in download_raw_dataset()."
        ) from exc

    df = dataset.to_pandas()
    df.to_parquet(raw_file, index=False)

    metadata = {
        "dataset_id": dataset_id,
        "split": split,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": len(df),
        "columns": list(df.columns),
        "source_mode": "huggingface",
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return raw_file


if __name__ == "__main__":
    file_path = download_raw_dataset()
    print(f"Raw dataset saved to: {file_path}")
