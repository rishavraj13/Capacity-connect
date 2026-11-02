"""Serialize enrollment lifecycle and sequential, idempotent station progress."""

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.services import require_approved_role
from apps.courses.constants import EnrollmentStatus
from apps.courses.exceptions import EnrollmentRuleError
from apps.courses.models import Course, Enrollment, Module, ModuleProgress


def _existing(trainee: User, course: Course) -> Enrollment | None:
    """Lock a persisted enrollment when reconciling duplicate requests."""
    return (
        Enrollment.objects.select_for_update()
        .filter(trainee=trainee, course=course)
        .first()
    )


def _activate(enrollment: Enrollment) -> Enrollment:
    """Reuse dropped history without reopening a completed enrollment."""
    if enrollment.status == EnrollmentStatus.COMPLETED:
        raise EnrollmentRuleError("Already completed.")
    if enrollment.status == EnrollmentStatus.DROPPED:
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.save(update_fields=["status", "updated_at"])
    return enrollment


@transaction.atomic
def enroll(trainee: User, course: Course) -> Enrollment:
    """Let the database arbitrate enrollment races inside a recoverable savepoint."""
    trainee = require_approved_role(trainee, (UserRole.TRAINEE,))
    course = Course.objects.select_for_update().get(pk=course.pk)
    require_approved_role(course.trainer, (UserRole.TRAINER,))
    if not course.is_published:
        raise EnrollmentRuleError("Only published courses accept enrollment.")
    existing = _existing(trainee, course)
    if existing:
        return _activate(existing)
    try:
        with transaction.atomic():
            return Enrollment.objects.create(trainee=trainee, course=course)
    except IntegrityError as exc:
        existing = _existing(trainee, course)
        if existing is None:
            raise EnrollmentRuleError(
                "Enrollment conflict; refresh and retry."
            ) from exc
        return _activate(existing)


def _owned_active(actor: User, enrollment: Enrollment) -> Enrollment:
    """Recheck current role, persisted ownership and lifecycle on each write."""
    actor = require_approved_role(actor, (UserRole.TRAINEE,))
    enrollment = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
    if enrollment.trainee_id != actor.pk:
        raise EnrollmentRuleError("Only the enrollment owner may change progress.")
    if enrollment.status != EnrollmentStatus.ACTIVE:
        raise EnrollmentRuleError("Enrollment must be active.")
    return enrollment


@transaction.atomic
def drop(actor: User, enrollment: Enrollment) -> Enrollment:
    """Preserve progress while ending active participation for its owner."""
    enrollment = _owned_active(actor, enrollment)
    enrollment.status = EnrollmentStatus.DROPPED
    enrollment.save(update_fields=["status", "updated_at"])
    return enrollment


@transaction.atomic
def complete_module(
    actor: User, enrollment: Enrollment, module: Module
) -> ModuleProgress:
    """Complete only the lowest unfinished station; final completion is deferred."""
    enrollment = _owned_active(actor, enrollment)
    module = Module.objects.get(pk=module.pk)
    if module.course_id != enrollment.course_id:
        raise EnrollmentRuleError("The module belongs to another course.")
    existing = ModuleProgress.objects.filter(
        enrollment=enrollment, module=module
    ).first()
    if existing:
        return existing
    next_module = (
        Module.objects.filter(course_id=enrollment.course_id)
        .exclude(progress__enrollment=enrollment)
        .first()
    )
    if next_module != module:
        raise EnrollmentRuleError("Complete modules in order.")
    return ModuleProgress.objects.create(
        enrollment=enrollment, module=module, completed_at=timezone.now()
    )
