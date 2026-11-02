"""Pin the shared percentage helper's units, rounding and empty denominator."""

from decimal import Decimal

import pytest

from apps.core.percentages import percent_for


@pytest.mark.parametrize(
    "score,total,expected",
    [(1, 3, "33.33"), (3, 4, "75.00"), (0, 0, "0.00"), (1, 32, "3.13")],
)
def test_shared_percentage_units(score: int, total: int, expected: str) -> None:
    """Keep the helper move from changing established grading units."""
    assert percent_for(score, total) == Decimal(expected)
