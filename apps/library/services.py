"""Manage private resources with shared ownership and commit-time file cleanup."""

from functools import partial

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.services import (
    assigned_trainer,
    require_approved_role,
    require_owner_or_admin,
)
from apps.core.services import validated_save
from apps.courses.models import Course
from apps.library.exceptions import ResourceRuleError
from apps.library.models import LibraryResource
from apps.library.validation import validate_resource_upload

RESOURCE_FIELDS = ("subject", "course", "title", "kind", "file", "description")


def _apply(resource: LibraryResource, data: dict) -> None:
    """Keep trainer and publication flags out of descriptive mass assignment."""
    for field in RESOURCE_FIELDS:
        if field in data:
            setattr(resource, field, data[field])


def _save(resource: LibraryResource) -> None:
    """Check the persisted course association and actual file bytes before saving."""
    if resource.course_id:
        course = Course.objects.filter(
            pk=resource.course_id,
            trainer_id=resource.trainer_id,
            subject_id=resource.subject_id,
        ).first()
        if course is None:
            raise ResourceRuleError(
                "Course must match the resource trainer and subject."
            )
    if not resource.file:
        raise ResourceRuleError("A resource file is required.")
    try:
        validate_resource_upload(resource.file, resource.kind)
    except ValidationError as exc:
        raise ResourceRuleError(" ".join(exc.messages)) from exc
    validated_save(resource, ResourceRuleError)


@transaction.atomic
def create_resource(actor: User, data: dict) -> LibraryResource:
    """Assign trainer ownership automatically unless an Admin selects the trainer."""
    resource = LibraryResource(trainer=assigned_trainer(actor, data))
    _apply(resource, data)
    _save(resource)
    return resource


@transaction.atomic
def update_resource(
    actor: User, resource: LibraryResource, data: dict
) -> LibraryResource:
    """Replace evidence without deleting the old bytes before database commit."""
    resource = LibraryResource.objects.select_for_update().get(pk=resource.pk)
    require_owner_or_admin(actor, resource.trainer_id)
    old = resource.file
    resource.trainer = assigned_trainer(actor, data, resource.trainer)
    _apply(resource, data)
    _save(resource)
    if old.name != resource.file.name:
        transaction.on_commit(partial(old.storage.delete, old.name))
    return resource


@transaction.atomic
def delete_resource(actor: User, resource: LibraryResource) -> None:
    """Remove private bytes only after their metadata deletion commits."""
    resource = LibraryResource.objects.select_for_update().get(pk=resource.pk)
    require_owner_or_admin(actor, resource.trainer_id)
    file = resource.file
    resource.delete()
    transaction.on_commit(partial(file.storage.delete, file.name))


@transaction.atomic
def _publication(
    actor: User, resource: LibraryResource, published: bool
) -> LibraryResource:
    """Keep publication flags on explicit role-checked actions."""
    resource = LibraryResource.objects.select_for_update().get(pk=resource.pk)
    require_owner_or_admin(actor, resource.trainer_id)
    if published:
        require_approved_role(resource.trainer, (UserRole.TRAINER,))
    resource.is_published = published
    resource.save(update_fields=["is_published", "updated_at"])
    return resource


def publish(actor: User, resource: LibraryResource) -> LibraryResource:
    """Expose a managed resource through approved portal visibility."""
    return _publication(actor, resource, True)


def unpublish(actor: User, resource: LibraryResource) -> LibraryResource:
    """Withdraw public portal access while retaining the owner's evidence."""
    return _publication(actor, resource, False)
