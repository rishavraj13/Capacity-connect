"""Populate quiz papers, results and participation at two rendered sizes."""

from functools import partial

from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import (
    AnswerFactory,
    AttemptFactory,
    QuestionFactory,
    QuestionnaireFactory,
)
from apps.core.tests.query_pages import PageSetup
from apps.courses.tests.factories import EnrollmentFactory


def _quiz(user: object) -> tuple:
    """Keep the trainee's list/departure/history metadata populated at both sizes."""
    quiz = QuestionnaireFactory(max_attempts=10)
    EnrollmentFactory(trainee=user, course=quiz.course)
    question = QuestionFactory(questionnaire=quiz)
    attempt = AttemptFactory(questionnaire=quiz, trainee=user, status="SUBMITTED")
    return quiz, question, attempt


def trainee_page(name: str) -> PageSetup:
    """Scale own quiz/course and attempt rows for the three trainee metadata pages."""
    user = UserFactory(approved_trainee=True)
    quiz, _, _ = _quiz(user)
    if name == "assessments:detail":
        expand = partial(
            AttemptFactory.create_batch,
            9,
            questionnaire=quiz,
            trainee=user,
            status="SUBMITTED",
        )
        url = reverse(name, args=[quiz.pk])
    else:
        expand = partial(_expand_quizzes, user)
        url = reverse(name)
    return PageSetup(url, user, expand)


def staff_page(name: str) -> PageSetup:
    """Grow managed quizzes/questions or participant/result rows as appropriate."""
    quiz = QuestionnaireFactory()
    QuestionFactory(questionnaire=quiz)

    add_participant = partial(_add_participant, quiz)
    add_participant()
    if name == "assessments:course_list":
        return PageSetup(
            reverse(name, args=[quiz.course_id]),
            quiz.trainer,
            lambda: QuestionnaireFactory.create_batch(9, course=quiz.course),
        )
    expand = (
        add_participant
        if name == "assessments:participation"
        else lambda: QuestionFactory(questionnaire=quiz)
    )
    return PageSetup(
        reverse(name, args=[quiz.pk]),
        quiz.trainer,
        lambda: [expand() for _ in range(9)],
    )


def attempt_result() -> PageSetup:
    """Grow answered questions with exhausted quota to exercise correct-text reads."""
    user = UserFactory(approved_trainee=True)
    quiz, question, attempt = _quiz(user)
    quiz.max_attempts = 1
    quiz.save()
    AnswerFactory(
        attempt=attempt, question=question, selected_option=question.options.first()
    )

    def add() -> None:
        """Add one result row and its protected selected option."""
        item = QuestionFactory(questionnaire=quiz)
        AnswerFactory(
            attempt=attempt, question=item, selected_option=item.options.first()
        )

    return PageSetup(
        reverse("assessments:result", args=[attempt.pk]),
        user,
        lambda: [add() for _ in range(9)],
    )


def _expand_quizzes(user: object) -> None:
    """Grow the list/history source using the same eligible trainee."""
    for _ in range(9):
        _quiz(user)


def _add_participant(quiz: object) -> None:
    """Provide eagerly joined result links and aggregate participation rows."""
    trainee = EnrollmentFactory(course=quiz.course).trainee
    AttemptFactory(questionnaire=quiz, trainee=trainee, status="SUBMITTED")
