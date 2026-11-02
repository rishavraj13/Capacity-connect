"""Build take-page data with no correctness-bearing fields or ORM objects."""

from datetime import timedelta

from apps.assessments.constants import AttemptStatus
from apps.assessments.dataclasses import PaperOption, PaperQuestion
from apps.assessments.models import Attempt, Option, Question
from apps.assessments.rules import expires_at
from apps.core import clock


def paper_for(attempt: Attempt) -> tuple[PaperQuestion, ...]:
    """Select only safe fields for a currently open attempt."""
    if not Attempt.objects.filter(
        pk=attempt.pk, status=AttemptStatus.IN_PROGRESS
    ).exists():
        return ()
    options = {}
    for question_id, option_id, text in Option.objects.filter(
        question__questionnaire_id=attempt.questionnaire_id
    ).values_list("question_id", "pk", "text"):
        options.setdefault(question_id, []).append(PaperOption(option_id, text))
    questions = Question.objects.filter(
        questionnaire_id=attempt.questionnaire_id
    ).values_list("pk", "text", "order", "marks")
    return tuple(
        PaperQuestion(pk, text, order, marks, tuple(options.get(pk, [])))
        for pk, text, order, marks in questions
    )


def seconds_left(attempt: Attempt) -> int:
    """Display a server-computed countdown value without client-side clock logic."""
    return max(0, (expires_at(attempt) - clock.now()) // timedelta(seconds=1))
