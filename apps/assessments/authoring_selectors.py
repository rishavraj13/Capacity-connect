"""Keep related assessment reads together without changing query behavior."""

from django.db.models import (
    QuerySet,
)

from apps.accounts.models import User
from apps.assessments.models import Question, Questionnaire
from apps.courses.selectors import managed_courses


def managed_questionnaires(user: User) -> QuerySet[Questionnaire]:
    """Hide another trainer's authoring objects before any detail/edit lookup."""
    return Questionnaire.objects.filter(
        course__in=managed_courses(user)
    ).select_related("course", "trainer", "subject")


def managed_questions(user: User) -> QuerySet[Question]:
    """Resolve question ownership through the parent quiz's course."""
    return Question.objects.filter(
        questionnaire__in=managed_questionnaires(user)
    ).select_related("questionnaire__course")


def authoring_detail(user: User, pk: int) -> QuerySet[Questionnaire]:
    """Prefetch answer-bearing choices only for authorized authoring pages."""
    return (
        managed_questionnaires(user)
        .filter(pk=pk)
        .prefetch_related("questions__options")
    )


def conflicting_course_questionnaire_subjects(
    course: object, subject: object
) -> QuerySet[Questionnaire]:
    """Keep derived assessment references consistent when course metadata changes."""
    return Questionnaire.objects.filter(course=course).exclude(subject=subject)


def question_initial(question: Question) -> dict:
    """Build a draft edit form from one ordered, owner-authorized option read."""
    options = list(question.options.all())
    return {
        "text": question.text,
        "marks": question.marks,
        "options": "\n".join(option.text for option in options),
        "correct_option": next(
            (index for index, option in enumerate(options, 1) if option.is_correct), 1
        ),
    }


def questionnaires_for_course(user: User, course: object) -> QuerySet[Questionnaire]:
    """Keep course-specific authoring list reads inside selectors."""
    return managed_questionnaires(user).filter(course=course)
