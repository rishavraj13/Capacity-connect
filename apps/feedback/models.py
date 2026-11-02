"""Protect feedback ownership and enforce exactly one reviewed target."""

from django.conf import settings
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models

from apps.core.models import TimeStampedModel
from apps.feedback.constants import MAX_COMMENT_LENGTH, MAX_RATING, MIN_RATING


class Feedback(TimeStampedModel):
    """Retain one editable opinion per trainee and target."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="feedback"
    )
    course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="feedback",
    )
    resource = models.ForeignKey(
        "library.LibraryResource",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="feedback",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)]
    )
    comment = models.TextField(
        max_length=MAX_COMMENT_LENGTH,
        blank=True,
        validators=[MaxLengthValidator(MAX_COMMENT_LENGTH)],
    )

    class Meta:
        """Keep direct writes within rating, target and uniqueness rules."""

        ordering = ("-created_at", "-pk")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=MIN_RATING, rating__lte=MAX_RATING),
                name="feedback_rating_bounds",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(course__isnull=False, resource__isnull=True)
                    | models.Q(course__isnull=True, resource__isnull=False)
                ),
                name="feedback_one_target",
            ),
            models.UniqueConstraint(
                fields=("author", "course"),
                condition=models.Q(course__isnull=False),
                name="unique_author_course_feedback",
            ),
            models.UniqueConstraint(
                fields=("author", "resource"),
                condition=models.Q(resource__isnull=False),
                name="unique_author_resource_feedback",
            ),
        ]
