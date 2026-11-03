"""Keep assessment ownership, readiness and elapsed-time rules in one place."""

from datetime import datetime, timedelta

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.services import require_approved_role, require_owner_or_admin
from apps.assessments.constants import (
    ATTEMPT_GRACE_SECONDS,
    ZERO_PERCENT,
    AttemptStatus,
)
from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.models import Attempt, Questionnaire
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Enrollment

START_WINDOW_ERROR = "Questionnaire is outside its start window."
QUOTA_ERROR = "Maximum attempts reached."
ENROLLMENT_ERROR = "An active enrollment is required."
READINESS_ERROR = "Questionnaire is not ready."


def managed_questionnaire(actor: User, questionnaire: Questionnaire) -> Questionnaire:
    """Lock authoring against starts and authorize the persisted course owner."""
    current = (
        Questionnaire.objects.select_for_update()
        .select_related("course")
        .get(pk=questionnaire.pk)
    )
    require_owner_or_admin(actor, current.course.trainer_id)
    return current


def require_editable_questions(questionnaire: Questionnaire) -> None:
    """Freeze question/option identities as soon as any attempt has existed."""
    if questionnaire.attempts.exists():
        raise AssessmentRuleError("Questions and options are frozen after any attempt.")


def require_enrollment(trainee: User, questionnaire: Questionnaire) -> User:
    """Permit existing ACTIVE participation even when the course is unpublished."""
    current = require_approved_role(trainee, (UserRole.TRAINEE,))
    if not Enrollment.objects.filter(
        trainee=current, course=questionnaire.course, status=EnrollmentStatus.ACTIVE
    ).exists():
        raise AssessmentRuleError(ENROLLMENT_ERROR)
    return current


def require_ready(questionnaire: Questionnaire) -> None:
    """Refuse starts until every question has a valid finite choice set."""
    from apps.assessments.readiness import ready_questionnaires

    if (
        not ready_questionnaires(questionnaire.course_id)
        .filter(pk=questionnaire.pk)
        .exists()
    ):
        raise AssessmentRuleError(READINESS_ERROR)


def start_window_state(questionnaire: Questionnaire, instant: datetime) -> str:
    """Use the same half-open start window in the service and presentation."""
    if instant < questionnaire.opens_at:
        return "Upcoming"
    if instant >= questionnaire.deadline:
        return "Closed"
    return ""


def quota_exhausted(questionnaire: Questionnaire, attempts_used: int) -> bool:
    """Count all persisted attempts toward the configured limit."""
    return attempts_used >= questionnaire.max_attempts


def attempt_deadline(started_at: datetime, duration_minutes: int) -> datetime:
    """Share the grace-inclusive deadline with the read-only attempt preview."""
    return started_at + timedelta(
        minutes=duration_minutes, seconds=ATTEMPT_GRACE_SECONDS
    )


def expires_at(attempt: Attempt) -> datetime:
    """Make the grace-inclusive submission limit identical across all callers."""
    return attempt_deadline(attempt.started_at, attempt.questionnaire.duration_minutes)


def is_expired(attempt: Attempt, instant: datetime) -> bool:
    """Keep exactly-at-limit submissions on time and one microsecond later late."""
    return instant > expires_at(attempt)


def owned_attempt(actor: User, attempt: Attempt) -> Attempt:
    """Lock the attempt itself without reversing the start-service lock order."""
    current = require_approved_role(actor, (UserRole.TRAINEE,))
    attempt = (
        Attempt.objects.select_for_update(of=("self",))
        .select_related("questionnaire__course")
        .get(pk=attempt.pk)
    )
    if attempt.trainee_id != current.pk:
        raise AssessmentRuleError("Only the attempt owner may submit.")
    return attempt


def finalize_timeout(attempt: Attempt, instant: datetime) -> Attempt:
    """Discard answers rather than grade an expired attempt."""
    attempt.answers.all().delete()
    attempt.status, attempt.score, attempt.percent, attempt.passed = (
        AttemptStatus.TIMED_OUT,
        0,
        ZERO_PERCENT,
        False,
    )
    attempt.submitted_at = instant
    attempt.save(
        update_fields=(
            "status",
            "score",
            "percent",
            "passed",
            "submitted_at",
            "updated_at",
        )
    )
    return attempt
