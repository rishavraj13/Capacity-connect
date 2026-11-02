"""Exercise exact start, duration/grace and independent deadline boundaries."""

from datetime import timedelta
from typing import Any

import pytest

from apps.assessments import services
from apps.assessments.constants import ATTEMPT_GRACE_SECONDS, AttemptStatus
from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.tests.factories import MOMENT, ready_quiz
from apps.core import clock

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "offset,allowed",
    [(-1, False), (0, True)],
    ids=["opens-minus-microsecond", "opens-exact"],
)
def test_start_open_boundary(offset: int, allowed: bool, monkeypatch: Any) -> None:
    """Make opening inclusive down to one microsecond."""
    quiz, _, trainee = ready_quiz(opens_at=MOMENT)
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(microseconds=offset))
    if allowed:
        assert services.start_attempt(trainee, quiz).started_at == MOMENT
    else:
        with pytest.raises(AssessmentRuleError, match="window"):
            services.start_attempt(trainee, quiz)


@pytest.mark.parametrize(
    "offset,allowed",
    [(-1, True), (0, False)],
    ids=["deadline-minus-microsecond", "deadline-exact"],
)
def test_start_deadline_boundary(offset: int, allowed: bool, monkeypatch: Any) -> None:
    """Make the deadline exclusive without rounding away microseconds."""
    quiz, _, trainee = ready_quiz(deadline=MOMENT)
    instant = MOMENT + timedelta(microseconds=offset)
    monkeypatch.setattr(clock, "now", lambda: instant)
    if allowed:
        assert services.start_attempt(trainee, quiz).started_at == instant
    else:
        with pytest.raises(AssessmentRuleError, match="window"):
            services.start_attempt(trainee, quiz)


@pytest.mark.parametrize(
    "offset,status",
    [(0, AttemptStatus.SUBMITTED), (1, AttemptStatus.TIMED_OUT)],
    ids=["grace-limit-exact", "grace-limit-plus-microsecond"],
)
def test_submission_grace_boundary(offset: int, status: str, monkeypatch: Any) -> None:
    """Accept the exact elapsed limit and time out one microsecond later."""
    quiz, question, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    limit = MOMENT + timedelta(
        minutes=quiz.duration_minutes,
        seconds=ATTEMPT_GRACE_SECONDS,
        microseconds=offset,
    )
    monkeypatch.setattr(clock, "now", lambda: limit)
    result = services.submit_attempt(
        trainee, attempt, {question.pk: question.options.first().pk}
    )
    assert result.status == status and result.submitted_at == limit
    assert result.answers.count() == (1 if status == AttemptStatus.SUBMITTED else 0)


def test_started_before_deadline_can_finish_after_deadline(monkeypatch: Any) -> None:
    """Keep submit eligibility tied to elapsed duration instead of the start window."""
    quiz, question, trainee = ready_quiz(deadline=MOMENT + timedelta(microseconds=1))
    attempt = services.start_attempt(trainee, quiz)
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(seconds=1))
    assert services.start_attempt(trainee, quiz).pk == attempt.pk
    result = services.submit_attempt(
        trainee, attempt, {question.pk: question.options.first().pk}
    )
    assert result.status == AttemptStatus.SUBMITTED
