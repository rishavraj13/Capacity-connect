"""Orchestrate the sole atomic completion transition without model signals."""

import logging

from django.db import transaction

from apps.certificates.exceptions import CertificateGenerationError
from apps.certificates.services import issue_certificate
from apps.core import clock
from apps.courses.completion_selectors import completion_status
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Enrollment

logger = logging.getLogger(__name__)


def _evaluate(enrollment: Enrollment) -> bool:
    """Lock current participation and use one conditional ACTIVE-to-COMPLETED write."""
    current = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
    if current.status != EnrollmentStatus.ACTIVE:
        return False
    status = completion_status(current)
    if not status.requirements_met:
        return False
    changed = Enrollment.objects.filter(
        pk=current.pk, status=EnrollmentStatus.ACTIVE
    ).update(status=EnrollmentStatus.COMPLETED, updated_at=clock.now())
    if not changed:
        return False
    if status.questionnaires:
        issue_certificate(current)
    return True


def evaluate_completion(enrollment: Enrollment) -> bool:
    """Rollback only completion/certificate work if expected PDF generation fails."""
    try:
        with transaction.atomic():
            return _evaluate(enrollment)
    except CertificateGenerationError:
        logger.exception(
            "Certificate generation failed for enrollment %s", enrollment.pk
        )
    return False


def evaluate_course_attempt(attempt: object) -> None:
    """Adapt an on-time passing result to the same enrollment completion entry."""
    enrollment = Enrollment.objects.filter(
        course_id=attempt.questionnaire.course_id,
        trainee_id=attempt.trainee_id,
        status=EnrollmentStatus.ACTIVE,
    ).first()
    if enrollment:
        evaluate_completion(enrollment)
