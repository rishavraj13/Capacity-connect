"""Centralize catalog writes so all entry points preserve lifecycle rules."""

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import Skill, Subject


def create_subject(data: dict[str, Any]) -> Subject:
    """Validate catalog names before creating a new line."""
    subject = Subject(
        name=data["name"].strip(), description=data.get("description", "")
    )
    subject.full_clean()
    subject.save()
    return subject


def update_subject(subject: Subject, data: dict[str, Any]) -> Subject:
    """Keep lifecycle flags outside editable subject details."""
    subject.name = data["name"].strip()
    subject.description = data.get("description", "")
    subject.full_clean()
    subject.save()
    return subject


def deactivate_subject(subject: Subject) -> None:
    """Retain references while stopping new skill assignments."""
    subject.is_active = False
    subject.save(update_fields=["is_active", "updated_at"])


def reactivate_subject(subject: Subject) -> None:
    """Restore an existing line without creating duplicate history."""
    subject.is_active = True
    subject.save(update_fields=["is_active", "updated_at"])


def _active_subject(subject: Subject) -> Subject:
    """Check current persisted state instead of trusting stale form objects."""
    current = Subject.objects.select_for_update().get(pk=subject.pk)
    if not current.is_active:
        raise ValidationError("Inactive subjects cannot receive skills.")
    return current


@transaction.atomic
def create_skill(data: dict[str, Any]) -> Skill:
    """Reject new skills on deactivated subjects at the write boundary."""
    subject = _active_subject(data["subject"])
    skill = Skill(name=data["name"].strip(), subject=subject)
    skill.full_clean()
    skill.save()
    return skill


@transaction.atomic
def update_skill(skill: Skill, data: dict[str, Any]) -> Skill:
    """Prevent moving skills onto retired subjects while permitting renames."""
    subject = data["subject"]
    if subject.pk != skill.subject_id:
        _active_subject(subject)
    skill.name, skill.subject = data["name"].strip(), subject
    skill.full_clean()
    skill.save()
    return skill


def delete_skill(skill: Skill) -> None:
    """Remove a catalog skill through the write layer."""
    skill.delete()
