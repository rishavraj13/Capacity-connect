"""Verify ownership, exactly-one option input and immutable attempt history."""

from datetime import timedelta

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments import services
from apps.assessments.dataclasses import QuestionInput
from apps.assessments.models import Option, Question, Questionnaire
from apps.assessments.tests.factories import (
    MOMENT,
    AttemptFactory,
    QuestionFactory,
    QuestionnaireFactory,
)
from apps.catalog.tests.factories import SubjectFactory
from apps.core.exceptions import CapacityConnectError

pytestmark = pytest.mark.django_db


def quiz_data(**changes: object) -> dict:
    """Keep authoring tests focused on their changed rule rather than date setup."""
    return {
        "title": "Quiz",
        "opens_at": MOMENT - timedelta(hours=1),
        "deadline": MOMENT + timedelta(hours=1),
        "duration_minutes": 5,
        "pass_percent": 50,
        "max_attempts": 2,
        **changes,
    }


def test_questionnaire_ownership_and_derived_fields() -> None:
    """Ignore submitted trainer identity and validate redundant subject association."""
    course = QuestionnaireFactory().course
    other = UserFactory(approved_trainer=True)
    quiz = services.create_questionnaire(
        course.trainer, course, quiz_data(trainer=other)
    )
    assert quiz.trainer == course.trainer and quiz.subject == course.subject
    with pytest.raises(CapacityConnectError):
        services.create_questionnaire(other, course, quiz_data())
    with pytest.raises(CapacityConnectError, match="Subject"):
        services.create_questionnaire(
            course.trainer, course, quiz_data(subject=SubjectFactory())
        )
    admin = UserFactory(active_admin=True)
    assert (
        services.update_questionnaire(admin, quiz, {"title": "Admin edit"}).title
        == "Admin edit"
    )
    with pytest.raises(CapacityConnectError):
        services.update_questionnaire(other, quiz, {"title": "Stolen"})


@pytest.mark.parametrize("count", [2, 6], ids=["two-options", "six-options"])
def test_add_update_question_exact_single_correct(count: int) -> None:
    """Create question and options together while keeping exactly one correct."""
    quiz = QuestionnaireFactory()
    data = QuestionInput("Choose", tuple(str(n) for n in range(count)), count - 1, 3)
    question = services.add_question(quiz.trainer, quiz, data)
    assert (
        question.options.count() == count
        and question.options.filter(is_correct=True).count() == 1
    )
    updated = services.update_question(
        quiz.trainer, question, QuestionInput("Edited", ("A", "B"), 0, 2)
    )
    assert updated.text == "Edited" and updated.marks == 2
    assert list(updated.options.values_list("text", "is_correct")) == [
        ("A", True),
        ("B", False),
    ]
    services.delete_question(quiz.trainer, updated)
    assert not Question.objects.exists() and not Option.objects.exists()


@pytest.mark.parametrize(
    "data",
    [
        QuestionInput("Q", ("A",), 0),
        QuestionInput("Q", tuple(str(i) for i in range(7)), 0),
        QuestionInput("Q", ("A", "B"), -1),
        QuestionInput("Q", ("A", "B"), 2),
        QuestionInput("", ("A", "B"), 0),
        QuestionInput("Q", ("", "B"), 0),
        QuestionInput("Q", ("A", "B"), 0, 0),
    ],
    ids=[
        "too-few",
        "too-many",
        "no-correct",
        "invalid-correct",
        "blank-question",
        "blank-option",
        "zero-marks",
    ],
)
def test_invalid_question_input_is_atomic(data: QuestionInput) -> None:
    """Reject invalid option sets without leaving a partial question behind."""
    quiz = QuestionnaireFactory()
    with pytest.raises(CapacityConnectError):
        services.add_question(quiz.trainer, quiz, data)
    assert not Question.objects.exists() and not Option.objects.exists()


def test_attempt_freezes_questions_options_marks_duration_and_pass_percent() -> None:
    """Keep every grading reference stable from the very first attempt."""
    question = QuestionFactory()
    quiz = question.questionnaire
    AttemptFactory(questionnaire=quiz)
    data = QuestionInput("Changed", ("X", "Y"), 0, 2)
    operations = [
        lambda: services.add_question(quiz.trainer, quiz, data),
        lambda: services.update_question(quiz.trainer, question, data),
        lambda: services.delete_question(quiz.trainer, question),
        lambda: services.delete_questionnaire(quiz.trainer, quiz),
    ]
    for operation in operations:
        with pytest.raises(CapacityConnectError, match="frozen"):
            operation()
    for data in ({"pass_percent": 51}, {"duration_minutes": 6}):
        with pytest.raises(CapacityConnectError, match="frozen"):
            services.update_questionnaire(quiz.trainer, quiz, data)


def test_scheduling_and_quota_can_change_after_attempt_but_quota_cannot_lower() -> None:
    """Allow scheduling changes and raised quota without rewriting grading terms."""
    quiz = QuestionnaireFactory(max_attempts=2)
    AttemptFactory(questionnaire=quiz)
    updated = services.update_questionnaire(
        quiz.trainer,
        quiz,
        {
            "opens_at": MOMENT,
            "deadline": MOMENT + timedelta(hours=2),
            "max_attempts": 3,
        },
    )
    assert updated.max_attempts == 3 and updated.opens_at == MOMENT
    with pytest.raises(CapacityConnectError, match="not lowered"):
        services.update_questionnaire(quiz.trainer, updated, {"max_attempts": 2})


def test_draft_deletion_removes_options_before_protected_parents() -> None:
    """Delete an unused questionnaire without relying on unapproved cascades."""
    question = QuestionFactory()
    services.delete_questionnaire(
        question.questionnaire.trainer, question.questionnaire
    )
    assert (
        not Questionnaire.objects.exists()
        and not Question.objects.exists()
        and not Option.objects.exists()
    )
