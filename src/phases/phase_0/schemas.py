from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class UserPreferenceInput(BaseModel):
    location: str = Field(min_length=2)
    budget: Union[float, str] = Field(
        description="Budget amount for two (numeric) or one of low|medium|high"
    )
    cuisine: str = Field(min_length=2)
    minimum_rating: float = Field(ge=0.0, le=5.0)
    additional_preferences: Optional[str] = None
    top_k: int = Field(default=50, ge=1, le=200)

    @field_validator("budget", mode="before")
    @classmethod
    def validate_budget(cls, value: object) -> Union[float, str]:
        if isinstance(value, (int, float)):
            if float(value) < 0:
                raise ValueError("budget amount must be >= 0")
            return float(value)
        normalized = str(value).strip().lower()
        if normalized in {"low", "medium", "high"}:
            return normalized
        try:
            numeric = float(normalized)
        except ValueError as exc:
            raise ValueError("budget must be numeric or one of: low, medium, high") from exc
        if numeric < 0:
            raise ValueError("budget amount must be >= 0")
        return numeric


class RestaurantRecord(BaseModel):
    restaurant_id: str
    name: str
    location_city: str
    locality: Optional[str] = None
    cuisines: List[str]
    avg_cost_for_two: Optional[float] = Field(default=None, ge=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    source_dataset: str = "ManikaSaini/zomato-restaurant-recommendation"


class CandidateRecord(BaseModel):
    restaurant_id: str
    name: str
    locality: Optional[str] = None
    cuisines: List[str]
    rating: Optional[float] = None
    avg_cost_for_two: Optional[float] = None
    candidate_score: float = Field(ge=0.0)
    score_breakdown: dict = Field(default_factory=dict)


class RecommendationItem(BaseModel):
    restaurant_name: str
    locality: Optional[str] = None
    cuisine: str
    rating: Optional[float] = None
    estimated_cost: Optional[float] = None
    explanation: str
    fit_score: int = Field(ge=0, le=100)


class RecommendationMetadata(BaseModel):
    prompt_version: str
    model_version: str
    data_version: str
    fallback_tier: str = "none"
    llm_used: bool = False


class RecommendationResponse(BaseModel):
    normalized_input: UserPreferenceInput
    recommendations: List[RecommendationItem]
    metadata: RecommendationMetadata
