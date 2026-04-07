from src.phases.phase_1.normalization import clamp_rating, parse_cuisines, parse_float


def test_parse_cuisines_splits_and_strips() -> None:
    assert parse_cuisines("Italian, Chinese,  North Indian ") == [
        "italian",
        "chinese",
        "north indian",
    ]


def test_parse_float_handles_currency_like_text() -> None:
    assert parse_float("1,200 INR") == 1200.0


def test_clamp_rating_limits_bounds() -> None:
    assert clamp_rating(6.1) == 5.0
    assert clamp_rating(-1.0) == 0.0
