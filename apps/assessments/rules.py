"""Keep assessment ownership, readiness and elapsed-time rules in one place."""

from datetime import datetime, timedelta

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.services import require_approved_role, require_owner_or_admin
from apps.assessments.constants import (
    ATTEMPT_GRACE_SECONDS,
    MAX_OPTIONS,
    MIN_OPTIONS,
    ZERO_PERCENT,
    AttemptStatus,
)
from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.models import Attempt, Question, Questionnaire
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Enrollment


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
        raise AssessmentRuleError("An active enrollment is required.")
    return current


def require_ready(questionnaire: Questionnaire) -> None:
    """Refuse starts until every question has a valid finite choice set."""
    questions = list(
        Question.objects.filter(questionnaire=questionnaire).prefetch_related("options")
    )
    if not questions:
        raise AssessmentRuleError("Questionnaire is not ready.")
    for question in questions:
        options = list(question.options.all())
        if (
            not MIN_OPTIONS <= len(options) <= MAX_OPTIONS
            or sum(option.is_correct for option in options) != 1
        ):
            raise AssessmentRuleError("Questionnaire is not ready.")


def expires_at(attempt: Attempt) -> datetime:
    """Make the grace-inclusive submission limit identical across all callers."""
    return attempt.started_at + timedelta(
        minutes=attempt.questionnaire.duration_minutes, seconds=ATTEMPT_GRACE_SECONDS
    )


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
