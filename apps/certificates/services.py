"""Issue one private PDF per eligible completion and recover identifier collisions."""

from datetime import date
from decimal import Decimal

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from reportlab.pdfbase.pdfdoc import PDFError

from apps.certificates.constants import ID_RETRY_LIMIT
from apps.certificates.exceptions import (
    CertificateGenerationError,
    CertificateRuleError,
)
from apps.certificates.issuance import average_for, grade_for, next_identifier, pdf_data
from apps.certificates.models import Certificate
from apps.certificates.pdf import render_certificate_pdf
from apps.core import clock
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Enrollment

GENERATION_ERRORS = (OSError, ValueError, TypeError, PDFError)


def _store_pdf(row: Certificate) -> Certificate:
    """Delete a just-written file if persisting its reference fails."""
    saved_name = None
    try:
        payload = render_certificate_pdf(pdf_data(row))
        row.pdf.save(f"{row.certificate_id}.pdf", ContentFile(payload), save=False)
        saved_name = row.pdf.name
        row.save(update_fields=["pdf", "updated_at"])
    except (*GENERATION_ERRORS, IntegrityError) as exc:
        if saved_name:
            _remove_failed_pdf(row, saved_name)
        raise CertificateGenerationError(
            "Certificate PDF generation failed; retry completion."
        ) from exc
    return row


def _insert(
    enrollment: Enrollment, average: Decimal, issued: date
) -> Certificate | None:
    """Rollback only a failed unique insert before examining a race winner."""
    try:
        with transaction.atomic():
            return Certificate.objects.create(
                enrollment=enrollment,
                certificate_id=next_identifier(issued.year),
                issued_on=issued,
                average_percent=average,
                grade=grade_for(average),
            )
    except IntegrityError:
        return None


@transaction.atomic
def issue_certificate(enrollment: Enrollment) -> Certificate:
    """Return a stored certificate unchanged or atomically create its PDF record."""
    enrollment = (
        Enrollment.objects.select_for_update(of=("self",))
        .select_related("trainee", "course__trainer")
        .get(pk=enrollment.pk)
    )
    existing = Certificate.objects.filter(enrollment=enrollment).first()
    if existing:
        return existing
    if enrollment.status != EnrollmentStatus.COMPLETED:
        raise CertificateRuleError(
            "Only a completed enrollment can receive a certificate."
        )
    average, issued = average_for(enrollment), clock.today()
    for _ in range(ID_RETRY_LIMIT):
        row = _insert(enrollment, average, issued)
        if row is not None:
            return _store_pdf(row)
        existing = Certificate.objects.filter(enrollment=enrollment).first()
        if existing:
            return existing
    raise CertificateGenerationError(
        "Certificate identifier conflict; retry completion."
    )


def _remove_failed_pdf(row: Certificate, name: str) -> None:
    """Keep secondary cleanup I/O failures inside the generation error boundary."""
    try:
        row.pdf.storage.delete(name)
    except OSError as exc:
        raise CertificateGenerationError(
            "Certificate cleanup failed; private-file cleanup is required before retry."
        ) from exc
