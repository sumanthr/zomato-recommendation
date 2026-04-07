from __future__ import annotations

from typing import Any


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def parse_cuisines(raw_value: Any) -> list[str]:
    value = normalize_text(raw_value)
    if not value:
        return []
    parts = [item.strip() for item in value.split(",")]
    return [item for item in parts if item]


def parse_float(raw_value: Any) -> float | None:
    text = normalize_text(raw_value)
    if not text:
        return None
    cleaned = text.replace(",", "")
    filtered = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    if not filtered:
        return None
    try:
        return float(filtered)
    except ValueError:
        return None


def clamp_rating(rating: float | None) -> float | None:
    if rating is None:
        return None
    return max(0.0, min(5.0, rating))
