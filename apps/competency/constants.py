"""Keep competency bounds and ranking weights in one exact Decimal table."""

from decimal import Decimal

MIN_PROFICIENCY = 1
MAX_PROFICIENCY = 5
MIN_YEARS = 0
MAX_YEARS = 60
W_PROFICIENCY = Decimal("0.40")
W_RATING = Decimal("0.30")
W_EXPERIENCE = Decimal("0.30")
MAX_RATING = 5
EXPERIENCE_CAP_YEARS = 10
SCORE_QUANTUM = Decimal("0.0001")

RANK_DECIMAL_PRECISION = 50
