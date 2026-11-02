"""Detach published board rows from mutable ORM state."""

from dataclasses import dataclass
from datetime import datetime

from apps.announcements.constants import Category


@dataclass(frozen=True, slots=True)
class BoardItem:
    """Expose only published announcement presentation fields."""

    id: int
    title: str
    body: str
    category: Category
    published_at: datetime
