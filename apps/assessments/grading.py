"""Validate the entire answer plan before any grade or answer write."""

from dataclasses import dataclass
from decimal import Decimal

from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.models import Attempt, Question
from apps.core.percentages import percent_for


@dataclass(frozen=True, slots=True)
class AnswerDecision:
    """Keep database-derived answer identity and correctness together."""

    question_id: int
    option_id: int
    is_correct: bool


@dataclass(frozen=True, slots=True)
class GradePlan:
    """Make validation precede persistence of every submitted answer."""

    answers: tuple[AnswerDecision, ...]
    score: int
    percent: Decimal
    passed: bool


def _selections(selections: dict) -> dict[int, int]:
    """Reject malformed IDs as a whole submission instead of leaking type errors."""
    try:
        return {int(question): int(option) for question, option in selections.items()}
    except (TypeError, ValueError) as exc:
        raise AssessmentRuleError("Invalid question or option ID.") from exc


def _answer_decision(question: Question, option_id: int) -> AnswerDecision:
    """Reject a mismatched option before any marks or rows are persisted."""
    option = next(
        (option for option in question.options.all() if option.pk == option_id), None
    )
    if option is None:
        raise AssessmentRuleError("An option does not belong to its question.")
    return AnswerDecision(question.pk, option_id, option.is_correct)


def grade_plan(attempt: Attempt, selections: dict) -> GradePlan:
    """Validate every relationship before computing any database-derived mark."""
    selected = _selections(selections)
    questions = list(
        Question.objects.filter(questionnaire=attempt.questionnaire).prefetch_related(
            "options"
        )
    )
    by_id = {question.pk: question for question in questions}
    if set(selected) - set(by_id):
        raise AssessmentRuleError("A question is outside this questionnaire.")
    answers, score = [], 0
    for question_id, option_id in selected.items():
        question = by_id[question_id]
        answer = _answer_decision(question, option_id)
        answers.append(answer)
        score += question.marks if answer.is_correct else 0
    percent = percent_for(score, sum(question.marks for question in questions))
    return GradePlan(
        tuple(answers), score, percent, percent >= attempt.questionnaire.pass_percent
    )
