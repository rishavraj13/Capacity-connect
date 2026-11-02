"""Prove protected assessment references and every named database constraint."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.assessments.constants import AttemptStatus
from apps.assessments.models import (
    Attempt,
    AttemptAnswer,
    Option,
    Question,
    Questionnaire,
)
from apps.assessments.tests.factories import (
    MOMENT,
    AnswerFactory,
    AttemptFactory,
    QuestionFactory,
    QuestionnaireFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "field,value",
    [
        ("deadline", MOMENT - timedelta(hours=1)),
        ("duration_minutes", 0),
        ("duration_minutes", 241),
        ("pass_percent", 0),
        ("pass_percent", 101),
        ("max_attempts", 0),
        ("max_attempts", 11),
    ],
    ids=[
        "window",
        "duration-low",
        "duration-high",
        "pass-low",
        "pass-high",
        "attempts-low",
        "attempts-high",
    ],
)
def test_questionnaire_database_bounds(field: str, value: object) -> None:
    """Enforce bounds independently of any form or service validation."""
    quiz = QuestionnaireFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        Questionnaire.objects.filter(pk=quiz.pk).update(**{field: value})
    assert str(quiz) == quiz.title


def test_question_order_marks_and_unique_database_rules() -> None:
    """Reject duplicate order and nonpositive question metadata directly in SQL."""
    question = QuestionFactory(order=1)
    for field in ("order", "marks"):
        with pytest.raises(IntegrityError), transaction.atomic():
            Question.objects.filter(pk=question.pk).update(**{field: 0})
    with pytest.raises(IntegrityError), transaction.atomic():
        Question.objects.create(
            questionnaire=question.questionnaire, text="Duplicate", order=1
        )


def test_at_most_one_correct_choice_partial_constraint() -> None:
    """Reject a second correct flag while allowing additional incorrect choices."""
    question = QuestionFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        Option.objects.create(question=question, text="Second correct", is_correct=True)
    Option.objects.create(question=question, text="Additional wrong", is_correct=False)


def test_one_open_attempt_partial_constraint() -> None:
    """Permit closed history while forbidding two simultaneous open attempts."""
    attempt = AttemptFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        Attempt.objects.create(
            questionnaire=attempt.questionnaire,
            trainee=attempt.trainee,
            started_at=MOMENT,
        )
    Attempt.objects.create(
        questionnaire=attempt.questionnaire,
        trainee=attempt.trainee,
        started_at=MOMENT,
        status=AttemptStatus.SUBMITTED,
    )


@pytest.mark.parametrize("percent", [Decimal("-0.01"), Decimal("100.01")])
def test_attempt_percent_database_bounds(percent: Decimal) -> None:
    """Prevent invalid grades from being persisted through direct writes."""
    attempt = AttemptFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        Attempt.objects.filter(pk=attempt.pk).update(percent=percent)


def test_answer_uniqueness_and_all_foreign_keys_protect() -> None:
    """Preserve every referenced identity in submitted assessment history."""
    answer = AnswerFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        AttemptAnswer.objects.create(
            attempt=answer.attempt,
            question=answer.question,
            selected_option=answer.selected_option,
            is_correct=False,
        )
    quiz = answer.attempt.questionnaire
    for target in (
        answer.attempt,
        answer.question,
        answer.selected_option,
        quiz,
        quiz.course,
        quiz.subject,
        quiz.trainer,
        answer.attempt.trainee,
    ):
        with pytest.raises(ProtectedError):
            target.delete()
