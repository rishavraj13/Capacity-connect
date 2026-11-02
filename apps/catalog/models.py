"""Keep reusable subjects and skills consistent at the database boundary."""

from django.db import models
from django.db.models.functions import Lower

from apps.catalog.constants import NAME_MAX_LENGTH
from apps.core.models import TimeStampedModel


class Subject(TimeStampedModel):
    """Retain subject history even after a line becomes inactive."""

    name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        """Enforce names independently of form validation."""

        ordering = ("name", "pk")
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_lower_subject_name")
        ]

    def __str__(self) -> str:
        """Give operators a recognizable label."""
        return self.name


class Skill(TimeStampedModel):
    """Protect subject references used by profile skill selections."""

    name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="skills"
    )

    class Meta:
        """Prevent concurrent requests from introducing case variants."""

        ordering = ("name", "pk")
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_lower_skill_name")
        ]

    def __str__(self) -> str:
        """Give forms a readable skill label."""
        return self.name
