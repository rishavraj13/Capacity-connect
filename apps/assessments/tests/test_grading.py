"""Verify integer/Decimal grading, whole-submission validation and idempotence."""

from datetime import timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest

from apps.assessments import services
from apps.assessments.constants import AttemptStatus
from apps.assessments.models import Attempt, AttemptAnswer
from apps.assessments.tests.factories import (
    MOMENT,
    AnswerFactory,
    QuestionFactory,
    ready_quiz,
)
from apps.core import clock
from apps.core.exceptions import CapacityConnectError

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "marks,expected,passed",
    [(5000, Decimal("50.00"), True), (4999, Decimal("49.99"), False)],
    ids=["exact-threshold-passes", "49-99-below-50-fails"],
)
def test_exact_pass_percent_boundary(
    marks: int, expected: Decimal, passed: bool
) -> None:
    """Compare the mandated two-decimal result against the exact pass threshold."""
    quiz, question, trainee = ready_quiz()
    question.marks = marks
    question.save()
    QuestionFactory(questionnaire=quiz, marks=10000 - marks)
    attempt = services.start_attempt(trainee, quiz)
    result = services.submit_attempt(
        trainee, attempt, {question.pk: question.options.first().pk}
    )
    assert result.percent == expected and result.passed is passed
    assert result.answers.count() == 1


def test_mixed_marks_wrong_and_unanswered_are_graded_from_database() -> None:
    """Use actual option flags and count missing questions in the denominator."""
    quiz, first, trainee = ready_quiz()
    first.marks = 2
    first.save()
    second = QuestionFactory(questionnaire=quiz, marks=3)
    QuestionFactory(questionnaire=quiz, marks=5)
    attempt = services.start_attempt(trainee, quiz)
    result = services.submit_attempt(
        trainee,
        attempt,
        {first.pk: first.options.first().pk, second.pk: second.options.last().pk},
    )
    assert (
        result.score == 2 and result.percent == Decimal("20.00") and not result.passed
    )
    assert (
        result.answers.count() == 2
        and result.answers.filter(is_correct=True).count() == 1
    )


def test_half_up_rounding_and_all_unanswered() -> None:
    """Round 3.125 to 3.13 without any float and store no unanswered rows."""
    quiz, question, trainee = ready_quiz(max_attempts=2)
    QuestionFactory(questionnaire=quiz, marks=31)
    first = services.start_attempt(trainee, quiz)
    assert services.submit_attempt(
        trainee, first, {question.pk: question.options.first().pk}
    ).percent == Decimal("3.13")
    second = services.start_attempt(trainee, quiz)
    result = services.submit_attempt(trainee, second, {})
    assert (
        result.score == 0
        and result.percent == Decimal("0.00")
        and not result.answers.exists()
    )


@pytest.mark.parametrize(
    "tamper",
    ["foreign-question", "foreign-option", "other-question-option", "malformed-id"],
)
def test_tampered_submission_is_rejected_whole(tamper: str) -> None:
    """Leave attempts and answers unchanged if any submitted choice is invalid."""
    quiz, question, trainee = ready_quiz()
    other = QuestionFactory(questionnaire=quiz)
    foreign = QuestionFactory()
    attempt = services.start_attempt(trainee, quiz)
    choices = {question.pk: question.options.first().pk}
    bad = {
        "foreign-question": (foreign.pk, foreign.options.first().pk),
        "foreign-option": (question.pk, foreign.options.first().pk),
        "other-question-option": (question.pk, other.options.first().pk),
        "malformed-id": ("not-id", "bad"),
    }
    key, value = bad[tamper]
    choices[key] = value
    with pytest.raises(CapacityConnectError):
        services.submit_attempt(trainee, attempt, choices)
    attempt.refresh_from_db()
    assert (
        attempt.status == AttemptStatus.IN_PROGRESS
        and not AttemptAnswer.objects.exists()
    )


def test_service_double_submit_returns_stored_result_unchanged() -> None:
    """Make a repeated submission a pure read even if its new payload is invalid."""
    quiz, question, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    first = services.submit_attempt(
        trainee, attempt, {question.pk: question.options.first().pk}
    )
    snapshot = Attempt.objects.values().get(pk=first.pk)
    second = services.submit_attempt(trainee, attempt, {"tampered": "payload"})
    assert (
        second.pk == first.pk and Attempt.objects.values().get(pk=first.pk) == snapshot
    )
    assert first.answers.count() == 1


def test_late_submission_discards_existing_answers_and_is_idempotent(
    monkeypatch: Any,
) -> None:
    """Reject all saved answers at timeout rather than award partial marks."""
    quiz, question, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    AnswerFactory(
        attempt=attempt, question=question, selected_option=question.options.first()
    )
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(hours=1))
    result = services.submit_attempt(
        trainee, attempt, {question.pk: question.options.first().pk}
    )
    snapshot = Attempt.objects.values().get(pk=result.pk)
    assert (
        result.status == AttemptStatus.TIMED_OUT
        and result.score == 0
        and not result.passed
    )
    assert not result.answers.exists()
    services.submit_attempt(trainee, result, {})
    assert Attempt.objects.values().get(pk=result.pk) == snapshot


def test_submit_race_returns_already_persisted_winner() -> None:
    """Recover the real unique-answer collision after a competing submit finalized."""
    quiz, question, trainee = ready_quiz()
    stale = services.start_attempt(trainee, quiz)
    winner = services.submit_attempt(
        trainee, stale, {question.pk: question.options.first().pk}
    )
    with patch("apps.assessments.services.owned_attempt", return_value=stale):
        recovered = services.submit_attempt(
            trainee, stale, {question.pk: question.options.first().pk}
        )
    assert recovered.pk == winner.pk and recovered.status == AttemptStatus.SUBMITTED
    assert recovered.answers.count() == 1
