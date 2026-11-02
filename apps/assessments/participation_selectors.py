"""Build complete enrollment participation with two size-independent queries."""

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, DecimalField, Exists, Max, OuterRef, Q, Value
from django.db.models.functions import Coalesce

from apps.accounts.models import User
from apps.assessments.constants import PERCENT_QUANTUM, ZERO_PERCENT, AttemptStatus
from apps.assessments.dataclasses import ParticipationRow, QuestionnaireStats
from apps.assessments.grading import percent_for
from apps.assessments.models import Attempt, Questionnaire
from apps.courses.models import Enrollment


def _enrollment_rows(questionnaire: Questionnaire) -> object:
    """Keep zero-attempt trainees while aggregating only this questionnaire."""
    target = Q(trainee__assessment_attempts__questionnaire=questionnaire)
    return (
        Enrollment.objects.filter(course_id=questionnaire.course_id)
        .select_related("trainee")
        .annotate(
            attempts_used=Count(
                "trainee__assessment_attempts", filter=target, distinct=True
            ),
            best_percent=Coalesce(
                Max("trainee__assessment_attempts__percent", filter=target),
                Value(ZERO_PERCENT),
                output_field=DecimalField(max_digits=5, decimal_places=2),
            ),
            has_passed=Exists(_passing_attempts(questionnaire)),
            last_attempt_at=Max(
                "trainee__assessment_attempts__started_at", filter=target
            ),
        )
    )


def _row(enrollment: object) -> ParticipationRow:
    """Detach display names and aggregate values before templates iterate."""
    return ParticipationRow(
        enrollment.trainee_id,
        enrollment.trainee.get_full_name() or enrollment.trainee.username,
        enrollment.attempts_used,
        enrollment.best_percent.quantize(PERCENT_QUANTUM),
        enrollment.has_passed,
        enrollment.last_attempt_at,
    )


def _stats(rows: tuple[ParticipationRow, ...]) -> QuestionnaireStats:
    """Use the user's chosen attempted-trainee denominators for both statistics."""
    attempted = [row for row in rows if row.attempts_used]
    passed = sum(row.passed for row in attempted)
    average = ZERO_PERCENT
    if attempted:
        average = (
            sum((row.best_percent for row in attempted), ZERO_PERCENT)
            / Decimal(len(attempted))
        ).quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP)
    rate = percent_for(passed, len(attempted)) if attempted else ZERO_PERCENT
    return QuestionnaireStats(len(rows), len(attempted), passed, average, rate)


def participation(
    user: User, questionnaire: Questionnaire
) -> tuple[tuple[ParticipationRow, ...], QuestionnaireStats] | None:
    """Authorize before reading participant aggregates, including zero attempts."""
    from apps.assessments.selectors import managed_questionnaires

    if not managed_questionnaires(user).filter(pk=questionnaire.pk).exists():
        return None
    rows = tuple(_row(enrollment) for enrollment in _enrollment_rows(questionnaire))
    return rows, _stats(rows)


def _passing_attempts(questionnaire: Questionnaire) -> object:
    """Correlate passing history to each enrolled trainee without another query."""
    return Attempt.objects.filter(
        questionnaire=questionnaire,
        trainee_id=OuterRef("trainee_id"),
        passed=True,
        status=AttemptStatus.SUBMITTED,
    )
