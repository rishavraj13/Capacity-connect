"""Keep related assessment reads together without changing query behavior."""

from django.db.models import (
    Count,
    Exists,
    F,
    OuterRef,
    Q,
    QuerySet,
    Value,
)
from django.db.models.functions import Greatest

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.assessments.constants import AttemptStatus
from apps.assessments.models import Attempt, Questionnaire


def owned_attempts(trainee: User) -> QuerySet[Attempt]:
    """Prevent guessed attempt IDs from reaching trainee read or submit flows."""
    attempts = Attempt.objects.select_related("questionnaire__course")
    if (
        not trainee.is_active
        or not trainee.is_approved
        or trainee.role != UserRole.TRAINEE
    ):
        return attempts.none()
    return attempts.filter(trainee=trainee)


def history_for(trainee: User) -> QuerySet[Attempt]:
    """Keep a trainee's entire attempt history in one joined query."""
    return owned_attempts(trainee).order_by("-started_at", "-pk")


def passed_questionnaire_ids(enrollment: object) -> set[int]:
    """Provide B5 a read-only completion handoff without issuing completion here."""
    return set(
        Attempt.objects.filter(
            trainee_id=enrollment.trainee_id,
            questionnaire__course_id=enrollment.course_id,
            passed=True,
            status=AttemptStatus.SUBMITTED,
        ).values_list("questionnaire_id", flat=True)
    )


def has_passed(trainee: User, questionnaire: Questionnaire) -> bool:
    """Reuse persisted successful outcomes for later completion logic."""
    return Attempt.objects.filter(
        trainee=trainee,
        questionnaire=questionnaire,
        passed=True,
        status=AttemptStatus.SUBMITTED,
    ).exists()


def result_history(user: User, questionnaire: Questionnaire) -> QuerySet[Attempt]:
    """Provide staff links to finalized results without per-row trainee lookups."""
    from apps.assessments.result_selectors import visible_results

    return (
        visible_results(user)
        .filter(questionnaire=questionnaire)
        .select_related("trainee")
    )


def completion_questionnaires(enrollment: object) -> QuerySet[Questionnaire]:
    """Join ready-quiz passing/usage requirements for the completion handoff."""
    from apps.assessments.readiness import ready_questionnaires

    attempts = Attempt.objects.filter(
        questionnaire_id=OuterRef("pk"), trainee_id=enrollment.trainee_id
    )
    return ready_questionnaires(enrollment.course_id).annotate(
        trainee_passed=Exists(
            attempts.filter(status=AttemptStatus.SUBMITTED, passed=True)
        ),
        attempts_left=Greatest(
            F("max_attempts")
            - Count("attempts", filter=Q(attempts__trainee_id=enrollment.trainee_id)),
            Value(0),
        ),
    )


def best_submitted_percents(enrollment: object) -> list:
    """Average only ready quizzes and retain missing grades for invariant checking."""
    from django.db.models import Max

    from apps.assessments.readiness import ready_questionnaires

    return list(
        ready_questionnaires(enrollment.course_id)
        .order_by()
        .annotate(
            best=Max(
                "attempts__percent",
                filter=Q(
                    attempts__trainee_id=enrollment.trainee_id,
                    attempts__status=AttemptStatus.SUBMITTED,
                ),
            )
        )
        .values_list("best", flat=True)
    )
