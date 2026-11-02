"""Keep course and module writes behind current role and ownership checks."""

from django.db import transaction
from django.db.models.deletion import ProtectedError

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.services import (
    assigned_trainer,
    require_approved_role,
    require_owner_or_admin,
)
from apps.core.services import validated_save
from apps.courses.enrollment_services import (
    complete_module as complete_module,
)
from apps.courses.enrollment_services import (
    drop as drop,
)
from apps.courses.enrollment_services import (
    enroll as enroll,
)
from apps.courses.exceptions import CourseRuleError
from apps.courses.models import Course, Module
from apps.courses.module_rules import locked_module, validate_module_order

COURSE_FIELDS = ("title", "description", "subject", "start_date", "end_date")
MODULE_FIELDS = ("title", "order")


def _subject_available(subject: object) -> None:
    """Recheck subject state instead of trusting an old form choice."""
    from apps.catalog.selectors import active_subjects

    if not active_subjects().filter(pk=subject.pk).exists():
        raise CourseRuleError(
            "New course subject assignments require an active subject."
        )


def _apply_course(course: Course, data: dict) -> None:
    """Keep publication and ownership outside descriptive mass assignment."""
    for field in COURSE_FIELDS:
        if field in data:
            setattr(course, field, data[field])


@transaction.atomic
def create_course(actor: User, data: dict) -> Course:
    """Assign the trainer at the service boundary and require an active subject."""
    trainer = assigned_trainer(actor, data)
    _subject_available(data["subject"])
    course = Course(trainer=trainer)
    _apply_course(course, data)
    validated_save(course, CourseRuleError)
    return course


@transaction.atomic
def update_course(actor: User, course: Course, data: dict) -> Course:
    """Authorize persisted ownership before applying any submitted changes."""
    from apps.library.selectors import conflicting_course_resources

    course = Course.objects.select_for_update().get(pk=course.pk)
    require_owner_or_admin(actor, course.trainer_id)
    trainer = assigned_trainer(actor, data, course.trainer)
    subject = data.get("subject", course.subject)
    if subject.pk != course.subject_id:
        _subject_available(subject)
    if conflicting_course_resources(course, trainer, subject).exists():
        raise CourseRuleError(
            "Update associated resources before changing course trainer or subject."
        )
    course.trainer = trainer
    _apply_course(course, data)
    validated_save(course, CourseRuleError)
    return course


@transaction.atomic
def _publication(actor: User, course: Course, published: bool) -> Course:
    """Serialize publication changes with enrollment eligibility checks."""
    course = Course.objects.select_for_update().get(pk=course.pk)
    require_owner_or_admin(actor, course.trainer_id)
    if published:
        require_approved_role(course.trainer, (UserRole.TRAINER,))
    course.is_published = published
    course.save(update_fields=["is_published", "updated_at"])
    return course


def publish(actor: User, course: Course) -> Course:
    """Make a managed course enrollable through an explicit action."""
    return _publication(actor, course, True)


def unpublish(actor: User, course: Course) -> Course:
    """Hide new access while preserving enrolled trainees' course visibility."""
    return _publication(actor, course, False)


@transaction.atomic
def add_module(actor: User, course: Course, data: dict) -> Module:
    """Keep module ownership derived from its managed course."""
    course = Course.objects.select_for_update().get(pk=course.pk)
    require_owner_or_admin(actor, course.trainer_id)
    validate_module_order(course, data["order"])
    module = Module(course=course, **{field: data[field] for field in MODULE_FIELDS})
    validated_save(module, CourseRuleError)
    module.skills.set(data.get("skills", []))
    return module


@transaction.atomic
def update_module(actor: User, module: Module, data: dict) -> Module:
    """Turn duplicate station orders into domain validation feedback."""
    module = locked_module(module)
    require_owner_or_admin(actor, module.course.trainer_id)
    validate_module_order(module.course, data.get("order", module.order), module)
    for field in MODULE_FIELDS:
        if field in data:
            setattr(module, field, data[field])
    validated_save(module, CourseRuleError)
    if "skills" in data:
        module.skills.set(data["skills"])
    return module


@transaction.atomic
def delete_module(actor: User, module: Module) -> None:
    """Protect progress history, including a concurrent completion write."""
    module = locked_module(module)
    require_owner_or_admin(actor, module.course.trainer_id)
    if module.progress.exists():
        raise CourseRuleError("A module with progress cannot be deleted.")
    try:
        module.delete()
    except ProtectedError as exc:
        raise CourseRuleError("A module with progress cannot be deleted.") from exc
