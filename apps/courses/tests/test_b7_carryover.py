"""Cover the remaining real completion no-op paths before hardening changes."""

from io import StringIO

import pytest
from django.core.management import call_command

from apps.assessments.tests.factories import MOMENT
from apps.certificates.models import Certificate
from apps.core import clock
from apps.courses.services import drop
from apps.courses.tests.completion_factories import completion_flow
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def test_passing_submit_without_active_enrollment_preserves_dropped_history(
    monkeypatch: object,
) -> None:
    """Allow finishing an owned open attempt without reopening dropped participation."""
    from apps.assessments import services

    monkeypatch.setattr(clock, "now", lambda: MOMENT)
    enrollment, _, quiz, question = completion_flow()
    attempt = services.start_attempt(enrollment.trainee, quiz)
    drop(enrollment.trainee, enrollment)
    result = services.submit_attempt(
        enrollment.trainee, attempt, {question.pk: question.options.first().pk}
    )
    enrollment.refresh_from_db()
    assert (
        result.passed
        and enrollment.status == "DROPPED"
        and not Certificate.objects.exists()
    )


def test_retry_command_unmet_candidate_is_checked_but_not_failed() -> None:
    """Count an unfinished ACTIVE course as pending rather than a generation failure."""
    EnrollmentFactory()
    output = StringIO()
    call_command("evaluate_completions", stdout=output)
    assert output.getvalue().strip() == "checked=1 completed=0 certificates=0 failed=0"
