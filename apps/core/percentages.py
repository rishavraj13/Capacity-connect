"""Share exact percentage units and rounding across grading and analytics."""

from decimal import ROUND_HALF_UP, Decimal

PERCENT_SCALE = Decimal("100")
PERCENT_QUANTUM = Decimal("0.01")
ZERO_PERCENT = Decimal("0.00")


def percent_for(score: int | Decimal, total: int | Decimal) -> Decimal:
    """Return a two-place Decimal percentage, with zero for an empty denominator."""
    if not total:
        return ZERO_PERCENT
    return (Decimal(score) * PERCENT_SCALE / Decimal(total)).quantize(
        PERCENT_QUANTUM, rounding=ROUND_HALF_UP
    )
