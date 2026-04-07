import os

from src.phases.phase_1.curate_dataset import curate_dataset
from src.phases.phase_1.download_dataset import download_raw_dataset


def run_phase1_pipeline() -> None:
    raw_file = download_raw_dataset(
        local_fallback_path=os.getenv("ZOMATO_LOCAL_RAW_PATH")
    )
    print(f"[Phase1] Raw dataset ready: {raw_file}")

    curated_outputs = curate_dataset(input_path=str(raw_file))
    print("[Phase1] Curated outputs:")
    for artifact in curated_outputs:
        print(f"- {artifact}")


if __name__ == "__main__":
    run_phase1_pipeline()
