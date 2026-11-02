"""Read completion requirements in two dataset-size-independent queries."""

from django.db.models import Count

from apps.assessments.selectors import completion_questionnaires
from apps.courses.completion_data import CompletionStatus, QuestionnaireCompletion
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Enrollment


def completion_status(enrollment: Enrollment) -> CompletionStatus:
    """Expose ready quizzes and progress without altering completed history."""
    current = Enrollment.objects.annotate(
        done=Count("progress", distinct=True),
        total=Count("course__modules", distinct=True),
    ).get(pk=enrollment.pk)
    quizzes = tuple(
        QuestionnaireCompletion(q.title, q.trainee_passed, q.attempts_left, q.deadline)
        for q in completion_questionnaires(current)
    )
    return CompletionStatus(
        current.done,
        current.total,
        quizzes,
        current.status == EnrollmentStatus.COMPLETED,
    )


def active_enrollments() -> object:
    """Stream retry candidates without loading certificate or user graphs."""
    return Enrollment.objects.filter(status=EnrollmentStatus.ACTIVE).order_by("pk")
