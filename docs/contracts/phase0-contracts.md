# Phase 0 Contracts

## Request Contract: `UserPreferenceInput`

```json
{
  "location": "Indiranagar",
  "budget": 1200,
  "cuisine": "Italian",
  "minimum_rating": 4.0,
  "additional_preferences": "family friendly",
  "top_k": 5
}
```

Validation rules:
- `location` should be locality (for example `Indiranagar`, `Koramangala`).
- `budget` should be numeric amount for two (legacy values `low | medium | high` still supported).
- `minimum_rating` must be in range `0.0..5.0`.
- `top_k` must be in range `1..20`.

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

## Response Contract: `RecommendationResponse`

```json
{
  "normalized_input": {
    "location": "indiranagar",
    "budget": "medium",
    "cuisine": "italian",
    "minimum_rating": 4.0,
    "additional_preferences": "family friendly",
    "top_k": 5
  },
  "recommendations": [
    {
      "restaurant_name": "Olive Bistro",
      "cuisine": "Italian",
      "rating": 4.4,
      "estimated_cost": 1800.0,
      "explanation": "Strong cuisine match with budget fit and high user rating.",
      "fit_score": 91
    }
  ],
  "metadata": {
    "prompt_version": "v1",
    "model_version": "gpt-4o-mini",
    "data_version": "2026-04-06",
    "fallback_tier": "none"
  }
}
```
