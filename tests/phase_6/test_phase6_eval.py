from pathlib import Path

from src.phases.phase_6.evaluator import run_offline_evaluation
from src.phases.phase_7.bootstrap_sample_data import ensure_sample_curated_dataset


def test_phase6_evaluation_generates_report(tmp_path: Path) -> None:
    ensure_sample_curated_dataset()
    report_path = tmp_path / "eval_report.json"
    report = run_offline_evaluation(output_path=str(report_path))
    assert report["total_scenarios"] >= 1
    assert report_path.exists()
