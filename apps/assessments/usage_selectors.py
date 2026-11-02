"""Keep related assessment reads together without changing query behavior."""

from django.db.models import (
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
)
from django.db.models.functions import Greatest

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.assessments.constants import DEPARTURE_LIMIT, AttemptStatus, DepartureStatus
from apps.assessments.dataclasses import Departure
from apps.assessments.models import Attempt, Questionnaire
from apps.core import clock
from apps.courses.constants import EnrollmentStatus


def _usage_metadata(
    quizzes: QuerySet[Questionnaire], trainee: User
) -> QuerySet[Questionnaire]:
    """Annotate all-status usage and successful results without separate reads."""
    attempts = Attempt.objects.filter(questionnaire=OuterRef("pk"), trainee=trainee)
    quizzes = quizzes.annotate(
        attempts_used=Count(
            "attempts", filter=Q(attempts__trainee=trainee), distinct=True
        ),
        already_passed=Exists(
            attempts.filter(passed=True, status=AttemptStatus.SUBMITTED)
        ),
    )
    return quizzes.annotate(
        open_attempt_id=Subquery(
            attempts.filter(status=AttemptStatus.IN_PROGRESS).values("pk")[:1]
        ),
        enrollment_status=F("course__enrollments__status"),
        attempts_left=Greatest(
            F("max_attempts") - F("attempts_used"),
            Value(0),
            output_field=IntegerField(),
        ),
    )


def trainee_questionnaires(trainee: User) -> QuerySet[Questionnaire]:
    """Include ACTIVE/COMPLETED enrollment metadata with one joined SQL query."""
    quizzes = Questionnaire.objects.select_related("course", "subject")
    if (
        not trainee.is_active
        or not trainee.is_approved
        or trainee.role != UserRole.TRAINEE
    ):
        return _usage_metadata(quizzes.none(), trainee)
    quizzes = quizzes.filter(
        course__enrollments__trainee=trainee,
        course__enrollments__status__in=(
            EnrollmentStatus.ACTIVE,
            EnrollmentStatus.COMPLETED,
        ),
    )
    return _usage_metadata(quizzes, trainee)


def startable_questionnaires(trainee: User) -> QuerySet[Questionnaire]:
    """Keep dropped/non-enrolled quiz IDs out of the start endpoint."""
    return trainee_questionnaires(trainee).filter(
        enrollment_status=EnrollmentStatus.ACTIVE
    )


def next_deadlines_for(
    trainee: User, limit: int = DEPARTURE_LIMIT
) -> tuple[Departure, ...]:
    """Build upcoming departures in a single annotated joined query."""
    instant = clock.now()
    quizzes = (
        startable_questionnaires(trainee)
        .filter(deadline__gt=instant, attempts_left__gt=0, already_passed=False)
        .order_by("deadline", "pk")[: max(0, limit)]
    )
    return tuple(
        Departure(
            q.pk,
            q.title,
            q.course.title,
            q.subject.name,
            q.opens_at,
            q.deadline,
            DepartureStatus.OPEN if q.opens_at <= instant else DepartureStatus.UPCOMING,
            q.attempts_left,
        )
        for q in quizzes
    )
