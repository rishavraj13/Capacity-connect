"""Core reusable abstract models."""

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model tracking creation and modification timestamps."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last modified.",
    )

    class Meta:
        """Model metadata options."""

        abstract = True
        ordering = ["-created_at"]
