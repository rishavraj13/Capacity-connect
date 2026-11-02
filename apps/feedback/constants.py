"""Keep feedback validation and pagination limits consistent."""

from decimal import Decimal

MIN_RATING = 1
MAX_RATING = 5
MAX_COMMENT_LENGTH = 2000
PAGE_SIZE = 20


RATING_QUANTUM = Decimal("0.01")
