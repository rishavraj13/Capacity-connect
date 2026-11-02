"""Keep quiz creation and frozen-history authoring atomic and owner-controlled."""

from django.db import transaction
from django.db.models import Max

from apps.accounts.models import User
from apps.accounts.services import require_owner_or_admin
from apps.assessments.constants import (
    FIRST_QUESTION_ORDER,
    MAX_OPTIONS,
    MIN_MARKS,
    MIN_OPTIONS,
)
from apps.assessments.dataclasses import QuestionInput
from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.models import Option, Question, Questionnaire
from apps.assessments.rules import managed_questionnaire, require_editable_questions
from apps.core.services import validated_save
from apps.courses.models import Course

QUESTIONNAIRE_FIELDS = (
    "title",
    "opens_at",
    "deadline",
    "duration_minutes",
    "pass_percent",
    "max_attempts",
)
FROZEN_FIELDS = ("duration_minutes", "pass_percent")


def validate_question_input(data: QuestionInput) -> None:
    """Enforce exactly one chosen correct option and a bounded nonempty option set."""
    if not MIN_OPTIONS <= len(data.options) <= MAX_OPTIONS:
        raise AssessmentRuleError("Each question needs 2 to 6 options.")
    if not 0 <= data.correct_index < len(data.options):
        raise AssessmentRuleError("Choose exactly one correct option.")
    if not data.text.strip() or any(not option.strip() for option in data.options):
        raise AssessmentRuleError("Question and option text cannot be empty.")
    if data.marks < MIN_MARKS:
        raise AssessmentRuleError("Marks must be positive.")


def _questionnaire_values(questionnaire: Questionnaire, data: dict) -> None:
    """Derive redundant ownership/subject fields instead of accepting forged values."""
    if (
        data.get("subject", questionnaire.course.subject).pk
        != questionnaire.course.subject_id
    ):
        raise AssessmentRuleError("Subject must match the course.")
    questionnaire.subject = questionnaire.course.subject
    questionnaire.trainer = questionnaire.course.trainer
    for field in QUESTIONNAIRE_FIELDS:
        if field in data:
            setattr(questionnaire, field, data[field])


@transaction.atomic
def create_questionnaire(actor: User, course: Course, data: dict) -> Questionnaire:
    """Create a course-owned quiz with server-derived subject and trainer."""
    course = Course.objects.select_for_update().get(pk=course.pk)
    require_owner_or_admin(actor, course.trainer_id)
    questionnaire = Questionnaire(course=course)
    _questionnaire_values(questionnaire, data)
    validated_save(questionnaire, AssessmentRuleError)
    return questionnaire


@transaction.atomic
def update_questionnaire(
    actor: User, questionnaire: Questionnaire, data: dict
) -> Questionnaire:
    """Preserve grading terms once an attempt exists while allowing scheduling edits."""
    questionnaire = managed_questionnaire(actor, questionnaire)
    if questionnaire.attempts.exists():
        if any(
            data.get(field, getattr(questionnaire, field))
            != getattr(questionnaire, field)
            for field in FROZEN_FIELDS
        ):
            raise AssessmentRuleError(
                "Pass percent and duration are frozen after any attempt."
            )
        if (
            data.get("max_attempts", questionnaire.max_attempts)
            < questionnaire.max_attempts
        ):
            raise AssessmentRuleError("Max attempts may be raised, not lowered.")
    _questionnaire_values(questionnaire, data)
    validated_save(questionnaire, AssessmentRuleError)
    return questionnaire


@transaction.atomic
def delete_questionnaire(actor: User, questionnaire: Questionnaire) -> None:
    """Remove a draft explicitly without discarding protected assessment history."""
    questionnaire = managed_questionnaire(actor, questionnaire)
    require_editable_questions(questionnaire)
    Option.objects.filter(question__questionnaire=questionnaire).delete()
    questionnaire.questions.all().delete()
    questionnaire.delete()


def _options(question: Question, data: QuestionInput) -> None:
    """Generate correctness exclusively from the validated single index."""
    Option.objects.bulk_create(
        [
            Option(
                question=question,
                text=text.strip(),
                is_correct=index == data.correct_index,
            )
            for index, text in enumerate(data.options)
        ]
    )


@transaction.atomic
def add_question(
    actor: User, questionnaire: Questionnaire, data: QuestionInput
) -> Question:
    """Create the question and its valid options as one atomic authoring write."""
    questionnaire = managed_questionnaire(actor, questionnaire)
    require_editable_questions(questionnaire)
    validate_question_input(data)
    maximum = questionnaire.questions.aggregate(value=Max("order"))["value"]
    question = Question(
        questionnaire=questionnaire,
        text=data.text.strip(),
        marks=data.marks,
        order=maximum + 1 if maximum is not None else FIRST_QUESTION_ORDER,
    )
    validated_save(question, AssessmentRuleError)
    _options(question, data)
    return question


@transaction.atomic
def update_question(actor: User, question: Question, data: QuestionInput) -> Question:
    """Replace draft choices only while no attempt can reference their identity."""
    question = Question.objects.select_related("questionnaire").get(pk=question.pk)
    managed_questionnaire(actor, question.questionnaire)
    require_editable_questions(question.questionnaire)
    validate_question_input(data)
    question.text, question.marks = data.text.strip(), data.marks
    validated_save(question, AssessmentRuleError)
    question.options.all().delete()
    _options(question, data)
    return question


@transaction.atomic
def delete_question(actor: User, question: Question) -> None:
    """Keep attempted question/option history undeletable."""
    question = Question.objects.select_related("questionnaire").get(pk=question.pk)
    managed_questionnaire(actor, question.questionnaire)
    require_editable_questions(question.questionnaire)
    question.options.all().delete()
    question.delete()


def reassign_course_questionnaires(course: Course, trainer: User) -> None:
    """Update derived quiz ownership inside the caller's course transaction."""
    Questionnaire.objects.filter(course=course).update(trainer=trainer)
