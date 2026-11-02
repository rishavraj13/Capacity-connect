"""Build a bounded public board independently of administrative draft reads."""

from django.db.models import F, Window
from django.db.models.functions import RowNumber

from apps.accounts.constants import UserRole
from apps.announcements.constants import (
    PER_CATEGORY,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    Category,
)
from apps.announcements.dataclasses import BoardItem
from apps.announcements.models import Announcement


def board(per_category: int = PER_CATEGORY) -> dict:
    """Select only published items with a per-category SQL window limit."""
    result = {category: [] for category in Category.values}
    if per_category <= 0:
        return {key: tuple(value) for key, value in result.items()}
    rows = (
        Announcement.objects.filter(is_published=True)
        .annotate(
            position=Window(
                RowNumber(),
                partition_by=[F("category")],
                order_by=[F("published_at").desc(), F("pk").desc()],
            )
        )
        .filter(position__lte=per_category)
        .order_by("-published_at", "-pk")
    )
    for row in rows:
        result[row.category].append(
            BoardItem(
                row.pk, row.title, row.body, Category(row.category), row.published_at
            )
        )
    return {key: tuple(value) for key, value in result.items()}


def manage_list(user: object, category: str = "", status: str = "") -> object:
    """Keep all draft reads behind an explicit eligible Admin scope."""
    rows = Announcement.objects.select_related("created_by")
    if not user.is_active or not user.is_approved or user.role != UserRole.ADMIN:
        return rows.none()
    if category in Category.values:
        rows = rows.filter(category=category)
    if status in (STATUS_DRAFT, STATUS_PUBLISHED):
        rows = rows.filter(is_published=status == STATUS_PUBLISHED)
    return rows
