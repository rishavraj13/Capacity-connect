"""Verify exact averaging, grade boundaries, sequence arbitration and snapshots."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.assessments.constants import AttemptStatus
from apps.assessments.tests.factories import AttemptFactory, QuestionnaireFactory
from apps.certificates.constants import ID_RETRY_LIMIT
from apps.certificates.exceptions import (
    CertificateGenerationError,
    CertificateRuleError,
)
from apps.certificates.issuance import grade_for
from apps.certificates.models import Certificate
from apps.certificates.services import issue_certificate
from apps.certificates.tests.factories import CertificateFactory
from apps.core import clock
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "percent,grade",
    [
        ("80.00", "A"),
        ("79.99", "B"),
        ("65.00", "B"),
        ("64.99", "C"),
        ("50.00", "C"),
        ("49.99", "D"),
    ],
)
def test_certificate_grade_boundaries(percent: str, grade: str) -> None:
    """Keep inclusive grade cutoffs and the completed-below-fifty D band stable."""
    assert grade_for(Decimal(percent)) == grade


def test_average_best_submitted_is_half_up_over_all_questionnaires() -> None:
    """Average 100 and 66.67 as 83.34, ignoring inferior/non-submitted grades."""
    enrollment = EnrollmentFactory(status="COMPLETED")
    first, second = [QuestionnaireFactory(course=enrollment.course) for _ in range(2)]
    for quiz, percent in ((first, "100.00"), (first, "50.00"), (second, "66.67")):
        AttemptFactory(
            questionnaire=quiz,
            trainee=enrollment.trainee,
            status=AttemptStatus.SUBMITTED,
            percent=Decimal(percent),
        )
    AttemptFactory(
        questionnaire=second,
        trainee=enrollment.trainee,
        status=AttemptStatus.TIMED_OUT,
        percent=100,
    )
    row = issue_certificate(enrollment)
    assert row.average_percent == Decimal("83.34") and row.grade == "A"


def test_missing_submitted_grade_contributes_zero() -> None:
    """Keep ignored draft questionnaires in the certificate denominator as agreed."""
    enrollment = EnrollmentFactory(status="COMPLETED")
    quiz = QuestionnaireFactory(course=enrollment.course)
    QuestionnaireFactory(course=enrollment.course)
    AttemptFactory(
        questionnaire=quiz,
        trainee=enrollment.trainee,
        status=AttemptStatus.SUBMITTED,
        percent=100,
    )
    assert issue_certificate(enrollment).average_percent == Decimal("50.00")


def test_idempotent_issuance_preserves_file_and_snapshot() -> None:
    """Avoid new files and preserve the original rendered names after edits."""
    enrollment = EnrollmentFactory(
        status="COMPLETED", trainee__first_name="OriginalName"
    )
    row = issue_certificate(enrollment)
    payload = row.pdf.read()
    enrollment.trainee.first_name = "ChangedName"
    enrollment.trainee.save()
    with patch("apps.certificates.services.render_certificate_pdf") as renderer:
        repeated = issue_certificate(enrollment)
    assert repeated.pk == row.pk and repeated.pdf.name == row.pdf.name
    assert b"OriginalName" in payload and b"ChangedName" not in payload
    renderer.assert_not_called()
    assert Certificate.objects.count() == 1


def test_identifier_sequence_and_year_rollover(monkeypatch: object) -> None:
    """Start a new local-year sequence while retaining older issued identifiers."""
    first = issue_certificate(EnrollmentFactory(status="COMPLETED"))
    second = issue_certificate(EnrollmentFactory(status="COMPLETED"))
    assert (
        first.certificate_id == "CC-2026-00001"
        and second.certificate_id == "CC-2026-00002"
    )
    monkeypatch.setattr(clock, "today", lambda: date(2027, 1, 1))
    next_year = issue_certificate(EnrollmentFactory(status="COMPLETED"))
    assert next_year.certificate_id == "CC-2027-00001" and next_year.issued_on == date(
        2027, 1, 1
    )


def test_identifier_collision_retries_real_unique_constraint() -> None:
    """Recover an actual duplicate identifier insert within a savepoint."""
    existing = CertificateFactory()
    enrollment = EnrollmentFactory(status="COMPLETED")
    with patch(
        "apps.certificates.services.next_identifier",
        side_effect=[existing.certificate_id, "CC-2026-90001"],
    ):
        row = issue_certificate(enrollment)
    assert row.certificate_id == "CC-2026-90001" and Certificate.objects.count() == 2


def test_identifier_retry_exhaustion_is_domain_error() -> None:
    """Leave no partial record when bounded unique collision recovery is exhausted."""
    existing = CertificateFactory()
    enrollment = EnrollmentFactory(status="COMPLETED")
    with patch(
        "apps.certificates.services.next_identifier",
        return_value=existing.certificate_id,
    ) as propose:
        with pytest.raises(CertificateGenerationError, match="conflict"):
            issue_certificate(enrollment)
    assert propose.call_count == ID_RETRY_LIMIT and Certificate.objects.count() == 1


def test_active_enrollment_cannot_receive_certificate() -> None:
    """Keep direct issuance behind the recorded completion transition."""
    with pytest.raises(CertificateRuleError):
        issue_certificate(EnrollmentFactory())
