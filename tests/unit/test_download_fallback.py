from pathlib import Path

import pandas as pd

from src.phases.phase_1.download_dataset import download_raw_dataset


def test_download_uses_local_fallback(tmp_path: Path) -> None:
    source_file = tmp_path / "source.parquet"
    df = pd.DataFrame([{"Restaurant Name": "Demo", "City": "Bangalore"}])
    df.to_parquet(source_file, index=False)

    out_dir = tmp_path / "raw"
    output_file = download_raw_dataset(
        output_dir=str(out_dir), local_fallback_path=str(source_file)
    )

    assert output_file.exists()
    assert (out_dir / "zomato_raw_metadata.json").exists()
