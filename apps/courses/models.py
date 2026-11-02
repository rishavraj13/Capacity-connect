"""Protect course history and concurrent enrollment integrity."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.constants import (
    FIRST_MODULE_ORDER,
    TITLE_MAX_LENGTH,
    EnrollmentStatus,
)


class Course(TimeStampedModel):
    """Retain subject and trainer references used by enrollment history."""

    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(
        "catalog.Subject", on_delete=models.PROTECT, related_name="courses"
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="courses"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)

    class Meta:
        """Reject reversed dates independently of form validation."""

        ordering = ("pk",)
        indexes = [
            models.Index(
                fields=["id"],
                condition=models.Q(is_published=True),
                name="course_published_pk_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="course_dates_ordered",
            )
        ]

    def __str__(self) -> str:
        """Give course choices a recognizable label."""
        return self.title


class Module(TimeStampedModel):
    """Keep course stations ordered uniquely from one onwards."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    order = models.PositiveIntegerField(
        validators=[MinValueValidator(FIRST_MODULE_ORDER)]
    )
    skills = models.ManyToManyField("catalog.Skill", blank=True, related_name="modules")

    class Meta:
        """Protect sequential station ordering during concurrent edits."""

        ordering = ("order", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("course", "order"), name="unique_course_module_order"
            ),
            models.CheckConstraint(
                condition=models.Q(order__gte=FIRST_MODULE_ORDER),
                name="module_order_at_least_one",
            ),
        ]

    def __str__(self) -> str:
        """Give station lists a readable label."""
        return self.title


class Enrollment(TimeStampedModel):
    """Reuse a trainee's enrollment when dropped participation resumes."""

    trainee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="enrollments"
    )
    status = models.CharField(
        max_length=max(map(len, EnrollmentStatus.values)),
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
    )

    class Meta:
        """Prevent duplicate participation rows even under concurrent requests."""

        ordering = ("pk",)
        indexes = [models.Index(fields=["status"], name="enrollment_status_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=("trainee", "course"), name="unique_trainee_course"
            )
        ]


class ModuleProgress(TimeStampedModel):
    """Record each completed station once while protecting its module history."""

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="progress"
    )
    module = models.ForeignKey(
        Module, on_delete=models.PROTECT, related_name="progress"
    )
    completed_at = models.DateTimeField()

    class Meta:
        """Keep repeated completion requests idempotent at the database boundary."""

        constraints = [
            models.UniqueConstraint(
                fields=("enrollment", "module"), name="unique_enrollment_module"
            )
        ]
