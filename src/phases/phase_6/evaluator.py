from __future__ import annotations

import json
from pathlib import Path

from src.phases.phase_0.schemas import UserPreferenceInput
from src.phases.phase_4.orchestrator import run_recommendation_orchestration


def run_offline_evaluation(
    scenario_path: str = "src/phases/phase_6/config/scenarios.json",
    output_path: str = "data/reports/phase6_eval_report.json",
) -> dict:
    scenarios = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
    results = []
    success = 0
    for scenario in scenarios:
        payload = UserPreferenceInput(**scenario["payload"])
        try:
            response = run_recommendation_orchestration(payload)
            rec_count = len(response.recommendations)
            success += 1 if rec_count > 0 else 0
            results.append(
                {
                    "scenario": scenario["name"],
                    "recommendation_count": rec_count,
                    "fallback_tier": response.metadata.fallback_tier,
                    "status": "ok",
                }
            )
        except Exception as exc:
            results.append(
                {"scenario": scenario["name"], "recommendation_count": 0, "status": f"error: {exc}"}
            )

    summary = {
        "total_scenarios": len(scenarios),
        "non_empty_recommendation_scenarios": success,
        "coverage_rate": round(success / max(1, len(scenarios)), 2),
        "results": results,
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    report = run_offline_evaluation()
    print(json.dumps(report, indent=2))
