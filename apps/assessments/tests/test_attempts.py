"""Verify resume, expiry, quota, eligibility and partial-unique race recovery."""

from datetime import timedelta
from unittest.mock import patch

import pytest

from apps.assessments import services
from apps.assessments.constants import ATTEMPT_GRACE_SECONDS, AttemptStatus
from apps.assessments.models import Attempt, Option
from apps.assessments.tests.factories import (
    MOMENT,
    AttemptFactory,
    ready_quiz,
)
from apps.core.exceptions import CapacityConnectError
from apps.courses.models import Enrollment
from apps.courses.services import unpublish

pytestmark = pytest.mark.django_db


def test_double_start_resumes_one_open_attempt() -> None:
    """Treat double-click and refresh as the same started lifecycle."""
    quiz, _, trainee = ready_quiz()
    first = services.start_attempt(trainee, quiz)
    second = services.start_attempt(trainee, quiz)
    assert first.pk == second.pk and Attempt.objects.count() == 1
    assert first.started_at == second.started_at == MOMENT


@pytest.mark.parametrize("status", [AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT])
def test_all_final_statuses_consume_attempt_quota(status: str) -> None:
    """Count every attempted lifecycle rather than only successful submissions."""
    quiz, _, trainee = ready_quiz()
    AttemptFactory(questionnaire=quiz, trainee=trainee, status=status)
    with pytest.raises(CapacityConnectError, match="Maximum"):
        services.start_attempt(trainee, quiz)


def test_expired_open_finalization_commits_when_max_reached() -> None:
    """Persist timeout even though the refused new start returns a domain error."""
    quiz, _, trainee = ready_quiz()
    expired = MOMENT - timedelta(
        minutes=quiz.duration_minutes, seconds=ATTEMPT_GRACE_SECONDS, microseconds=1
    )
    attempt = AttemptFactory(questionnaire=quiz, trainee=trainee, started_at=expired)
    with pytest.raises(CapacityConnectError, match="Maximum"):
        services.start_attempt(trainee, quiz)
    attempt.refresh_from_db()
    assert attempt.status == AttemptStatus.TIMED_OUT and attempt.submitted_at == MOMENT
    assert attempt.percent == 0 and not attempt.passed and Attempt.objects.count() == 1


def test_expired_open_counts_used_then_allows_next_quota_slot() -> None:
    """Close the old lifecycle before creating a replacement open attempt."""
    quiz, _, trainee = ready_quiz(max_attempts=2)
    expired = MOMENT - timedelta(hours=1)
    old = AttemptFactory(questionnaire=quiz, trainee=trainee, started_at=expired)
    new = services.start_attempt(trainee, quiz)
    old.refresh_from_db()
    assert old.status == AttemptStatus.TIMED_OUT and new.pk != old.pk
    assert Attempt.objects.count() == 2


def test_open_attempt_unique_race_returns_winner() -> None:
    """Hit the real partial unique constraint after a simulated stale open read."""
    quiz, _, trainee = ready_quiz(max_attempts=2)
    winner = AttemptFactory(questionnaire=quiz, trainee=trainee)
    with patch("apps.assessments.services._open_attempt", side_effect=[None, winner]):
        assert services.start_attempt(trainee, quiz).pk == winner.pk
    assert Attempt.objects.count() == 1


def test_open_race_without_recoverable_winner_is_domain_error() -> None:
    """Keep failed partial-constraint recovery from exposing an IntegrityError."""
    quiz, _, trainee = ready_quiz(max_attempts=2)
    AttemptFactory(questionnaire=quiz, trainee=trainee)
    with patch("apps.assessments.services._open_attempt", return_value=None):
        with pytest.raises(CapacityConnectError, match="conflict"):
            services.start_attempt(trainee, quiz)
    assert Attempt.objects.count() == 1


@pytest.mark.parametrize("status", ["DROPPED", "COMPLETED", "absent"])
def test_start_requires_active_enrollment(status: str) -> None:
    """Reject dropped, completed and missing participation at the service boundary."""
    quiz, _, trainee = ready_quiz()
    if status == "absent":
        Enrollment.objects.filter(trainee=trainee).delete()
    else:
        Enrollment.objects.filter(trainee=trainee).update(status=status)
    with pytest.raises(CapacityConnectError, match="active enrollment"):
        services.start_attempt(trainee, quiz)


def test_enrolled_unpublished_course_can_still_start_quiz() -> None:
    """Complete the carry-over access contract without admitting new enrollments."""
    quiz, _, trainee = ready_quiz()
    unpublish(quiz.course.trainer, quiz.course)
    assert services.start_attempt(trainee, quiz).status == AttemptStatus.IN_PROGRESS


@pytest.mark.parametrize("invalid", ["empty", "one-option", "no-correct", "too-many"])
def test_not_ready_questionnaire_cannot_start(invalid: str) -> None:
    """Check all readiness rules before creating an attempt row."""
    quiz, question, trainee = ready_quiz()
    if invalid == "empty":
        question.options.all().delete()
        question.delete()
    elif invalid == "one-option":
        question.options.filter(is_correct=False).delete()
    elif invalid == "no-correct":
        question.options.update(is_correct=False)
    else:
        Option.objects.bulk_create(
            [Option(question=question, text=str(i)) for i in range(5)]
        )
    with pytest.raises(CapacityConnectError, match="not ready"):
        services.start_attempt(trainee, quiz)
    assert not Attempt.objects.exists()
