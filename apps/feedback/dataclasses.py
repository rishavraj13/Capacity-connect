"""Detach feedback comments from privileged author identity."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class FeedbackSummary:
    """Carry exact summary math and all five rating buckets."""

    count: int
    average: Decimal
    distribution: dict[int, int]


@dataclass(frozen=True, slots=True)
class FeedbackRow:
    """Make author names structurally absent for owning trainers."""

    rating: int
    comment: str
    author_name: str | None
