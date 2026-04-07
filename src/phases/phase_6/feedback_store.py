from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


def append_feedback(
    helpful: bool, reason: str, output_path: str = "data/reports/phase6_feedback.csv"
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp_utc", "helpful", "reason"])
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "helpful": helpful,
                "reason": reason,
            }
        )
