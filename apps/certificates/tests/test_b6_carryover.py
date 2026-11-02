"""Pin reviewer changes before replacing the earlier certificate denominator."""

from decimal import Decimal

import pytest

from apps.assessments.tests.factories import (
    AttemptFactory,
    QuestionFactory,
    QuestionnaireFactory,
)
from apps.certificates.services import issue_certificate
from apps.core.exceptions import CapacityConnectError
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def test_ready_quiz_and_empty_draft_average_is_100() -> None:
    """Exclude draft questionnaires instead of diluting a completed learner's score."""
    enrollment = EnrollmentFactory(status="COMPLETED")
    quiz = QuestionFactory(questionnaire__course=enrollment.course).questionnaire
    QuestionnaireFactory(course=enrollment.course)
    AttemptFactory(
        questionnaire=quiz,
        trainee=enrollment.trainee,
        status="SUBMITTED",
        percent=100,
        passed=True,
    )
    assert issue_certificate(enrollment).average_percent == Decimal("100.00")


def test_missing_ready_quiz_submission_is_domain_error() -> None:
    """Refuse inconsistent completed history rather than inventing a zero grade."""
    enrollment = EnrollmentFactory(status="COMPLETED")
    QuestionFactory(questionnaire__course=enrollment.course)
    with pytest.raises(CapacityConnectError, match="submitted"):
        issue_certificate(enrollment)
