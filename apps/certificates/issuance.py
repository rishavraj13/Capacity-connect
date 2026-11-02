"""Build certificate identifiers and immutable PDF inputs from locked records."""

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

from apps.certificates.constants import (
    GRADE_BANDS,
    ID_PREFIX,
    MAX_SEQUENCE,
    PERCENT_QUANTUM,
    ZERO_PERCENT,
)
from apps.certificates.dataclasses import CertificateData
from apps.certificates.exceptions import CertificateGenerationError
from apps.certificates.models import Certificate


def grade_for(percent: Decimal) -> str:
    """Keep every grade boundary in the single GRADE_BANDS table."""
    return next(grade for minimum, grade in GRADE_BANDS if percent >= minimum)


def average_for(enrollment: object) -> Decimal:
    """Include all course quizzes, using zero for a missing submitted attempt."""
    from apps.assessments.selectors import best_submitted_percents

    values = best_submitted_percents(enrollment)
    total = sum(
        (value if value is not None else ZERO_PERCENT for value in values), ZERO_PERCENT
    )
    return (
        (total / Decimal(len(values))).quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP)
        if values
        else ZERO_PERCENT
    )


def next_identifier(year: int) -> str:
    """Let the unique constraint arbitrate identical per-year sequence proposals."""
    prefix = f"{ID_PREFIX}-{year:04}-"
    highest = (
        Certificate.objects.filter(certificate_id__startswith=prefix)
        .order_by("-certificate_id")
        .values_list("certificate_id", flat=True)
        .first()
    )
    sequence = int(highest.rsplit("-", 1)[1]) + 1 if highest else 1
    if sequence > MAX_SEQUENCE:
        raise CertificateGenerationError(
            "Certificate sequence exhausted for this year."
        )
    return f"{prefix}{sequence:05}"


def pdf_data(row: Certificate) -> CertificateData:
    """Snapshot current display names and the absolute public URL into the PDF."""
    enrollment = row.enrollment
    trainee = enrollment.trainee
    trainer = enrollment.course.trainer
    return CertificateData(
        trainee.get_full_name() or trainee.username,
        enrollment.course.title,
        trainer.get_full_name() or trainer.username,
        settings.CERTIFICATE_SIGNATORY_NAME,
        settings.CERTIFICATE_SIGNATORY_TITLE,
        row.certificate_id,
        row.issued_on,
        row.average_percent,
        row.grade,
        f"{settings.SITE_BASE_URL.rstrip('/')}/verify/{row.certificate_id}/",
    )
