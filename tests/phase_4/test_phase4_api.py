from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from src.phases.phase_4.api import app


def _seed_curated_data(path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "restaurant_id": "1",
                "name": "Pasta Point",
                "location_city": "Bangalore",
                "locality": "Indiranagar",
                "cuisines": ["italian"],
                "avg_cost_for_two": 1200.0,
                "rating": 4.4,
            }
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_recommendations_endpoint_with_fallback(tmp_path: Path, monkeypatch) -> None:
    curated = tmp_path / "restaurants.parquet"
    _seed_curated_data(curated)
    monkeypatch.setenv("CURATED_DATA_PATH", str(curated))

    # Prevent external API dependency in this API test.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    client = TestClient(app)
    payload = {
        "location": "Bangalore",
        "budget": "medium",
        "cuisine": "Italian",
        "minimum_rating": 4.0,
        "top_k": 1,
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "recommendations" in body
    assert "metadata" in body
    assert body["metadata"]["llm_used"] is False


def test_localities_endpoint_and_options_preflight() -> None:
    # Uses whatever curated data path is active in runtime.
    client = TestClient(app)
    loc_response = client.get("/localities")
    assert loc_response.status_code == 200
    assert "localities" in loc_response.json()

    preflight = client.options(
        "/recommendations",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code in {200, 204}
