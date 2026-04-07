# Phase 0 Contracts

This document matches the Pydantic models in `src/phases/phase_0/schemas.py` and the live API behavior in `src/phases/phase_4/api.py`.

## Request Contract: `UserPreferenceInput`

```json
{
  "location": "Indiranagar",
  "budget": 1200,
  "cuisine": "North Indian",
  "minimum_rating": 4.0,
  "additional_preferences": null,
  "top_k": 50
}
```

Validation rules:

- `location`: **locality** string (minimum length 2). The backend normalizes against the curated locality inventory (exact match preferred, then fuzzy).
- `budget`: numeric **maximum cost for two** (amount in INR), or legacy categorical `low` | `medium` | `high`. Numeric values must be `>= 0`.
- `cuisine`: free text (minimum length 2); matched against parsed cuisine lists from the dataset.
- `minimum_rating`: `0.0` … `5.0`.
- `top_k`: integer `1` … `200` (default in schema is `50`; the UI may send a fixed upper value to return “all relevant” rows up to that cap).

## Data Contract: `RestaurantRecord`

```json
{
  "restaurant_id": "16774318",
  "name": "Olive Bistro",
  "location_city": "Bangalore",
  "locality": "Indiranagar",
  "cuisines": ["italian", "continental"],
  "avg_cost_for_two": 1800.0,
  "rating": 4.4,
  "source_dataset": "ManikaSaini/zomato-restaurant-recommendation"
}
```

## Candidate Contract: `CandidateRecord`

```json
{
  "restaurant_id": "16774318",
  "name": "Olive Bistro",
  "locality": "Indiranagar",
  "cuisines": ["italian", "continental"],
  "rating": 4.4,
  "avg_cost_for_two": 1800.0,
  "candidate_score": 0.87,
  "score_breakdown": {
    "rating": 0.4,
    "cuisine_match": 0.3,
    "budget_fit": 0.17
  }
}
```

`locality` is populated from the curated table for display and deduplication.

## Response Contract: `RecommendationResponse`

```json
{
  "normalized_input": {
    "location": "Indiranagar",
    "budget": 1200,
    "cuisine": "north indian",
    "minimum_rating": 4.0,
    "additional_preferences": null,
    "top_k": 50
  },
  "recommendations": [
    {
      "restaurant_name": "Olive Bistro",
      "locality": "Indiranagar",
      "cuisine": "Italian",
      "rating": 4.4,
      "estimated_cost": 1800.0,
      "explanation": "Optional text when LLM path is used; may be a short fallback string when ranking is deterministic.",
      "fit_score": 91
    }
  ],
  "metadata": {
    "prompt_version": "v1",
    "model_version": "llama-3.1-8b-instant",
    "data_version": "2026-04-07",
    "fallback_tier": "strict"
  }
}
```

Notes:

- `metadata.model_version` comes from env `LLM_MODEL` (Groq).
- `metadata.fallback_tier` reflects retrieval outcome (e.g. `strict`, `no_candidates`).
- The React UI may hide `explanation` and show only dataset-grounded fields.
