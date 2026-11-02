"""Keep resource visibility and association reads out of HTTP controllers."""

from django.db.models import Q, QuerySet

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.library.models import LibraryResource


def visible_resources(
    user: User, subject: object = None, kind: str | None = None
) -> QuerySet[LibraryResource]:
    """Let only owners/Admin inspect unpublished resources."""
    resources = LibraryResource.objects.select_related("trainer", "subject", "course")
    if not user.is_authenticated or not user.is_active or not user.is_approved:
        return resources.none()
    if user.role != UserRole.ADMIN:
        resources = resources.filter(Q(is_published=True) | Q(trainer=user))
    if subject is not None:
        resources = resources.filter(subject=subject)
    if kind:
        resources = resources.filter(kind=kind)
    return resources


def managed_resources(user: User) -> QuerySet[LibraryResource]:
    """Hide another trainer's resources before mutation lookups."""
    resources = visible_resources(user)
    if user.role == UserRole.ADMIN:
        return resources
    return (
        resources.filter(trainer=user)
        if user.role == UserRole.TRAINER
        else resources.none()
    )


def conflicting_course_resources(
    course: object, trainer: User, subject: object
) -> QuerySet[LibraryResource]:
    """Prevent course edits from breaking established resource associations."""
    return LibraryResource.objects.filter(course=course).exclude(
        trainer=trainer, subject=subject
    )


def detail_context(user: User, resource: LibraryResource) -> dict:
    """Avoid exposing linked unpublished course metadata through a public resource."""
    from apps.courses.selectors import visible_courses

    course_visible = (
        resource.course_id is not None
        and visible_courses(user).filter(pk=resource.course_id).exists()
    )
    return {"resource": resource, "course_visible": course_visible}
