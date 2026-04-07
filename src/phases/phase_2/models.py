from __future__ import annotations

from dataclasses import dataclass, field

from src.phases.phase_0.schemas import CandidateRecord, UserPreferenceInput


@dataclass
class NormalizedPreference:
    location_city: str
    location_match_confidence: float
    budget: str
    cuisine: str
    minimum_rating: float
    additional_preferences: str | None
    top_k: int
    normalization_confidence: float


@dataclass
class RetrievalResult:
    normalized_input: UserPreferenceInput
    normalized_context: NormalizedPreference
    candidates: list[CandidateRecord]
    fallback_tier: str
    fallback_reason: str
    stage_latency_ms: dict[str, int] = field(default_factory=dict)
