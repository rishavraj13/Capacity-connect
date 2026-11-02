"""Detach ranked display rows from lazy ORM reads."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RankedTrainer:
    """Expose rounded display scores only after exact ordering is resolved."""

    trainer_id: int
    name: str
    proficiency: int
    years_experience: int
    avg_rating: Decimal | None
    rating_count: int
    courses_delivered: int
    score: Decimal
    rank: int
