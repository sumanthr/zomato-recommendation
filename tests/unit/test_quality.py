import pandas as pd

from src.phases.phase_1.quality import generate_quality_report


def test_quality_report_passes_for_clean_data() -> None:
    df = pd.DataFrame(
        [
            {
                "name": "A",
                "location_city": "Bangalore",
                "locality": "Indiranagar",
                "cuisines": ["italian"],
                "rating": 4.2,
                "avg_cost_for_two": 1500,
            },
            {
                "name": "B",
                "location_city": "Bangalore",
                "locality": "Koramangala",
                "cuisines": ["north indian"],
                "rating": 4.0,
                "avg_cost_for_two": 900,
            },
        ]
    )
    report = generate_quality_report(df)
    assert report.checks_passed is True
