"""Retain manually authored notices with an explicit publication invariant."""

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models

from apps.announcements.constants import BODY_MAX_LENGTH, TITLE_MAX_LENGTH, Category
from apps.core.models import TimeStampedModel


class Announcement(TimeStampedModel):
    """Keep drafts hidden until an Admin explicitly publishes them."""

    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    body = models.TextField(
        max_length=BODY_MAX_LENGTH, validators=[MaxLengthValidator(BODY_MAX_LENGTH)]
    )
    category = models.CharField(
        max_length=max(map(len, Category.values)), choices=Category.choices
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="announcements"
    )

    class Meta:
        """Require a publication timestamp for every visible item."""

        ordering = ("-published_at", "-pk")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_published=False)
                | models.Q(published_at__isnull=False),
                name="announcement_published_timestamp",
            )
        ]
