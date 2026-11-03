"""Serialize assessment starts, expiry and one-transaction submission grading."""

from datetime import datetime

from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.assessments.authoring import (
    add_question as add_question,
)
from apps.assessments.authoring import (
    create_questionnaire as create_questionnaire,
)
from apps.assessments.authoring import (
    delete_question as delete_question,
)
from apps.assessments.authoring import (
    delete_questionnaire as delete_questionnaire,
)
from apps.assessments.authoring import (
    update_question as update_question,
)
from apps.assessments.authoring import (
    update_questionnaire as update_questionnaire,
)
from apps.assessments.constants import AttemptStatus
from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.grading import GradePlan, grade_plan
from apps.assessments.models import Attempt, AttemptAnswer, Questionnaire
from apps.assessments.rules import (
    QUOTA_ERROR,
    START_WINDOW_ERROR,
    finalize_timeout,
    is_expired,
    owned_attempt,
    quota_exhausted,
    require_enrollment,
    require_ready,
    start_window_state,
)
from apps.core import clock


def _open_attempt(trainee: User, questionnaire: Questionnaire) -> Attempt | None:
    """Read current persisted open state under the questionnaire start lock."""
    return (
        Attempt.objects.select_for_update()
        .select_related("questionnaire")
        .filter(
            trainee=trainee,
            questionnaire=questionnaire,
            status=AttemptStatus.IN_PROGRESS,
        )
        .first()
    )


def _insert_start(
    trainee: User, questionnaire: Questionnaire, instant: datetime
) -> Attempt | AssessmentRuleError:
    """Recover a competing open attempt after rolling back only the failed insert."""
    try:
        with transaction.atomic():
            return Attempt.objects.create(
                trainee=trainee, questionnaire=questionnaire, started_at=instant
            )
    except IntegrityError:
        return _open_attempt(trainee, questionnaire) or AssessmentRuleError(
            "Attempt conflict; retry."
        )


def _new_start(
    trainee: User, questionnaire: Questionnaire, instant: datetime
) -> Attempt | AssessmentRuleError:
    """Apply new-row eligibility without rolling back an earlier timeout."""
    if start_window_state(questionnaire, instant):
        return AssessmentRuleError(START_WINDOW_ERROR)
    if quota_exhausted(
        questionnaire, questionnaire.attempts.filter(trainee=trainee).count()
    ):
        return AssessmentRuleError(QUOTA_ERROR)
    try:
        require_ready(questionnaire)
    except AssessmentRuleError as exc:
        return exc
    return _insert_start(trainee, questionnaire, instant)


def _start_locked(
    trainee: User, questionnaire: Questionnaire
) -> Attempt | AssessmentRuleError:
    """Commit expired-open finalization even when the next start is refused."""
    questionnaire = Questionnaire.objects.select_for_update().get(pk=questionnaire.pk)
    trainee = require_enrollment(trainee, questionnaire)
    instant = clock.now()
    existing = _open_attempt(trainee, questionnaire)
    if existing and not is_expired(existing, instant):
        return existing
    if existing:
        finalize_timeout(existing, instant)
    return _new_start(trainee, questionnaire, instant)


def start_attempt(trainee: User, questionnaire: Questionnaire) -> Attempt:
    """Use one outer transaction and report refusal only after timeout commits."""
    with transaction.atomic():
        outcome = _start_locked(trainee, questionnaire)
    if isinstance(outcome, AssessmentRuleError):
        raise outcome
    return outcome


@transaction.atomic
def expire_attempt(trainee: User, attempt: Attempt) -> Attempt:
    """Apply the explicitly requested lazy expiry before rendering a take page."""
    attempt = owned_attempt(trainee, attempt)
    instant = clock.now()
    if attempt.status == AttemptStatus.IN_PROGRESS and is_expired(attempt, instant):
        return finalize_timeout(attempt, instant)
    return attempt


SUBMISSION_FIELDS = (
    "score",
    "percent",
    "passed",
    "status",
    "submitted_at",
    "updated_at",
)


def _answer_rows(attempt: Attempt, plan: GradePlan) -> list[AttemptAnswer]:
    """Construct only answered-question rows from the fully validated plan."""
    return [
        AttemptAnswer(
            attempt=attempt,
            question_id=answer.question_id,
            selected_option_id=answer.option_id,
            is_correct=answer.is_correct,
        )
        for answer in plan.answers
    ]


def _persist_submission(attempt: Attempt, plan: GradePlan, instant: datetime) -> None:
    """Keep answer insertion and grade inside the outer transaction's savepoint."""
    with transaction.atomic():
        AttemptAnswer.objects.bulk_create(_answer_rows(attempt, plan))
        attempt.score, attempt.percent, attempt.passed = (
            plan.score,
            plan.percent,
            plan.passed,
        )
        attempt.status, attempt.submitted_at = AttemptStatus.SUBMITTED, instant
        attempt.save(update_fields=SUBMISSION_FIELDS)
    if attempt.passed:
        _evaluate_completion(attempt)


@transaction.atomic
def submit_attempt(trainee: User, attempt: Attempt, selections: dict) -> Attempt:
    """Grade every answer atomically or return a stored final outcome unchanged."""
    attempt = owned_attempt(trainee, attempt)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        return attempt
    instant = clock.now()
    if is_expired(attempt, instant):
        return finalize_timeout(attempt, instant)
    plan = grade_plan(attempt, selections)
    try:
        _persist_submission(attempt, plan, instant)
    except IntegrityError as exc:
        winner = Attempt.objects.get(pk=attempt.pk)
        if winner.status == AttemptStatus.IN_PROGRESS:
            raise AssessmentRuleError("Submission conflict; retry.") from exc
        return winner
    return attempt


def _evaluate_completion(attempt: Attempt) -> None:
    """Keep the trigger adapter lazy while completion owns the transition rule."""
    from apps.courses.completion import evaluate_course_attempt

    evaluate_course_attempt(attempt)
