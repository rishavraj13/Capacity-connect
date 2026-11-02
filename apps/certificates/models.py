"""Retain a single protected certificate and its private PDF per completion."""

from django.db import models

from apps.certificates.constants import (
    ID_PREFIX,
    MAX_PERCENT,
    PDF_EXTENSIONS,
    PDF_FOLDER,
    ZERO_PERCENT,
    Grade,
)
from apps.core.models import TimeStampedModel
from apps.core.storage import PrivateStorage
from apps.core.uploads import UploadPath


class Certificate(TimeStampedModel):
    """Keep the issued PDF as an immutable snapshot of completion."""

    enrollment = models.OneToOneField(
        "courses.Enrollment", on_delete=models.PROTECT, related_name="certificate"
    )
    certificate_id = models.CharField(
        max_length=len(f"{ID_PREFIX}-0000-00000"), unique=True
    )
    issued_on = models.DateField()
    average_percent = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=1, choices=Grade.choices)
    pdf = models.FileField(
        storage=PrivateStorage(), upload_to=UploadPath(PDF_FOLDER, PDF_EXTENSIONS)
    )

    class Meta:
        """Protect aggregate percent even when the service is bypassed."""

        ordering = ("-issued_on", "-pk")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    average_percent__gte=ZERO_PERCENT, average_percent__lte=MAX_PERCENT
                ),
                name="certificate_percent_bounds",
            )
        ]
