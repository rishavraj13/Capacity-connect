"""Pin percentage units and attempted-trainee rounding independently of SQL."""

from decimal import Decimal

import pytest

from apps.assessments.dataclasses import ParticipationRow
from apps.assessments.participation_selectors import _stats


@pytest.mark.parametrize(
    "passed,total,expected", [(3, 4, "75.00"), (1, 3, "33.33"), (0, 0, "0.00")]
)
def test_statistics_use_two_decimal_percent_units(
    passed: int, total: int, expected: str
) -> None:
    """Keep the denominator clarification from changing percentage units."""
    rows = tuple(
        ParticipationRow(i, str(i), 1, Decimal("75.00"), i < passed, None)
        for i in range(total)
    )
    stats = _stats(rows)
    assert stats.pass_rate_percent == Decimal(expected)
    assert stats.average_best_percent == (
        Decimal("75.00") if total else Decimal("0.00")
    )
