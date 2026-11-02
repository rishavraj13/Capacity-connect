"""Keep every manual publication transition explicit and Admin-controlled."""

from django.db import transaction

from apps.accounts.constants import UserRole
from apps.accounts.services import require_approved_role
from apps.announcements.exceptions import AnnouncementRuleError
from apps.announcements.models import Announcement
from apps.core import clock
from apps.core.services import validated_save


def _managed(user: object, row: Announcement) -> Announcement:
    """Recheck persisted Admin eligibility and lock the current publication state."""
    require_approved_role(user, (UserRole.ADMIN,))
    return Announcement.objects.select_for_update().get(pk=row.pk)


def _values(row: Announcement, data: dict) -> None:
    """Keep author identity and publication state outside descriptive form input."""
    for name in ("title", "body", "category"):
        if name in data:
            setattr(row, name, data[name])


@transaction.atomic
def create(user: object, data: dict) -> Announcement:
    """Create drafts only, regardless of forged publication/author fields."""
    user = require_approved_role(user, (UserRole.ADMIN,))
    row = Announcement(created_by=user)
    _values(row, data)
    validated_save(row, AnnouncementRuleError)
    return row


@transaction.atomic
def update(user: object, row: Announcement, data: dict) -> Announcement:
    """Edit manual content while publication follows its separate POST actions."""
    row = _managed(user, row)
    _values(row, data)
    validated_save(row, AnnouncementRuleError)
    return row


@transaction.atomic
def publish(user: object, row: Announcement) -> Announcement:
    """Stamp each unpublished-to-published transition and leave repeats unchanged."""
    row = _managed(user, row)
    if row.is_published:
        return row
    row.is_published = True
    row.published_at = clock.now()
    row.save(update_fields=["is_published", "published_at", "updated_at"])
    return row


@transaction.atomic
def unpublish(user: object, row: Announcement) -> Announcement:
    """Hide immediately while retaining the latest publication timestamp."""
    row = _managed(user, row)
    if row.is_published:
        row.is_published = False
        row.save(update_fields=["is_published", "updated_at"])
    return row


@transaction.atomic
def delete(user: object, row: Announcement) -> None:
    """Let only an eligible Admin remove manually authored content."""
    _managed(user, row).delete()
