"""Apply owner/trainer/Admin result visibility before building safe result data."""

from django.db.models import Prefetch

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.assessments.constants import AttemptStatus
from apps.assessments.dataclasses import AttemptResult, ResultQuestion
from apps.assessments.models import Attempt, Option, Question


def visible_results(user: User) -> object:
    """Filter cross-owner result IDs before reading any answer rows."""
    attempts = Attempt.objects.exclude(status=AttemptStatus.IN_PROGRESS).select_related(
        "questionnaire__course"
    )
    if not user.is_active or not user.is_approved:
        return attempts.none()
    if user.role == UserRole.ADMIN:
        return attempts
    if user.role == UserRole.TRAINER:
        return attempts.filter(questionnaire__course__trainer=user)
    return (
        attempts.filter(trainee=user)
        if user.role == UserRole.TRAINEE
        else attempts.none()
    )


def _result_questions(attempt: Attempt, reveal: bool) -> tuple[ResultQuestion, ...]:
    """Avoid carrying correct-choice text at all when further attempts remain."""
    answers = {
        answer.question_id: answer
        for answer in attempt.answers.select_related("selected_option")
    }
    questions = Question.objects.filter(questionnaire_id=attempt.questionnaire_id)
    if reveal:
        correct = Option.objects.filter(is_correct=True).only(
            "pk", "question_id", "text"
        )
        questions = questions.prefetch_related(
            Prefetch("options", queryset=correct, to_attr="correct_options")
        )
    return tuple(
        _result_row(question, answers.get(question.pk), reveal)
        for question in questions
    )


def _result_row(question: Question, answer: object, reveal: bool) -> ResultQuestion:
    """Keep hidden correct text out of the returned result structure."""
    correct_text = (
        question.correct_options[0].text
        if reveal and question.correct_options
        else None
    )
    return ResultQuestion(
        question.pk,
        question.text,
        question.marks,
        answer.selected_option.text if answer else None,
        bool(answer and answer.is_correct),
        correct_text,
    )


def attempt_result(user: User, attempt_id: int) -> AttemptResult | None:
    """Reveal correct choices to staff or a trainee with exhausted current quota."""
    attempt = visible_results(user).filter(pk=attempt_id).first()
    if attempt is None:
        return None
    used = Attempt.objects.filter(
        questionnaire_id=attempt.questionnaire_id, trainee_id=attempt.trainee_id
    ).count()
    reveal = (
        user.role in (UserRole.TRAINER, UserRole.ADMIN)
        or used >= attempt.questionnaire.max_attempts
    )
    return AttemptResult(
        attempt.pk,
        attempt.questionnaire.title,
        attempt.score,
        attempt.percent,
        attempt.passed,
        attempt.status,
        _result_questions(attempt, reveal),
    )
