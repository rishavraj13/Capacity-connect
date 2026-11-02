"""Protect trainer declarations and their subject history."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.competency.constants import (
    MAX_PROFICIENCY,
    MAX_YEARS,
    MIN_PROFICIENCY,
    MIN_YEARS,
)
from apps.core.models import TimeStampedModel


class TrainerCompetency(TimeStampedModel):
    """Retain one bounded self-declaration per trainer and subject."""

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="competencies"
    )
    subject = models.ForeignKey(
        "catalog.Subject", on_delete=models.PROTECT, related_name="competencies"
    )
    proficiency = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_PROFICIENCY),
            MaxValueValidator(MAX_PROFICIENCY),
        ]
    )
    years_experience = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_YEARS), MaxValueValidator(MAX_YEARS)]
    )

    class Meta:
        """Keep duplicate declarations and invalid ranges out of direct DB writes."""

        ordering = ("subject__name", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("trainer", "subject"), name="unique_trainer_subject_competency"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    proficiency__gte=MIN_PROFICIENCY, proficiency__lte=MAX_PROFICIENCY
                ),
                name="competency_proficiency_bounds",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    years_experience__gte=MIN_YEARS, years_experience__lte=MAX_YEARS
                ),
                name="competency_experience_bounds",
            ),
        ]
