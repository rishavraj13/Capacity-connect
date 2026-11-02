"""Reuse one SQL readiness predicate for starts and course completion."""

from django.db.models import Count, Exists, OuterRef, Q, QuerySet

from apps.assessments.constants import MAX_OPTIONS, MIN_OPTIONS
from apps.assessments.models import Question, Questionnaire


def ready_questionnaires(course_id: int) -> QuerySet[Questionnaire]:
    """Require questions and reject any invalid option set without per-quiz reads."""
    questions = Question.objects.filter(questionnaire_id=OuterRef("pk"))
    invalid = questions.annotate(
        option_count=Count("options"),
        correct_count=Count("options", filter=Q(options__is_correct=True)),
    ).filter(
        Q(option_count__lt=MIN_OPTIONS)
        | Q(option_count__gt=MAX_OPTIONS)
        | ~Q(correct_count=1)
    )
    return (
        Questionnaire.objects.filter(course_id=course_id)
        .annotate(has_questions=Exists(questions), invalid_questions=Exists(invalid))
        .filter(has_questions=True, invalid_questions=False)
    )
