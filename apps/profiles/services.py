"""Keep profile creation, allowlisted writes and storage cleanup together."""

from functools import partial
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.catalog.selectors import selectable_skills
from apps.profiles.constants import (
    ACCOUNT_FIELDS,
    CERTIFICATE_FIELDS,
    EXPERIENCE_FIELDS,
    QUALIFICATION_FIELDS,
    TRAINEE_FIELDS,
    TRAINER_FIELDS,
)
from apps.profiles.models import (
    ExternalCertificate,
    Qualification,
    TraineeProfile,
    TrainerProfile,
    WorkExperience,
)

CHILD_FIELDS = {
    Qualification: QUALIFICATION_FIELDS,
    WorkExperience: EXPERIENCE_FIELDS,
    ExternalCertificate: CERTIFICATE_FIELDS,
}


def ensure_trainee_profile(user: User) -> TraineeProfile:
    """Create trainee details lazily without discarding history on role changes."""
    if user.role != UserRole.TRAINEE:
        raise ValidationError("A trainee role is required.")
    return TraineeProfile.objects.get_or_create(user=user)[0]


def ensure_trainer_profile(user: User) -> TrainerProfile:
    """Create trainer details lazily without introducing signals."""
    if user.role != UserRole.TRAINER:
        raise ValidationError("A trainer role is required.")
    return TrainerProfile.objects.get_or_create(user=user)[0]


def _save_fields(instance: Any, data: dict, fields: tuple) -> Any:
    """Ignore privileged inputs and delete replaced files only after commit."""
    file_field = "file" if isinstance(instance, ExternalCertificate) else "photo"
    old = (
        getattr(type(instance).objects.get(pk=instance.pk), file_field, None)
        if instance.pk
        else None
    )
    for field in fields:
        if field in data:
            setattr(
                instance,
                field,
                data[field] or "" if field == file_field else data[field],
            )
    instance.full_clean()
    instance.save()
    current = getattr(instance, file_field, None)
    if old and old.name != getattr(current, "name", None):
        transaction.on_commit(partial(old.storage.delete, old.name))
    return instance


@transaction.atomic
def update_trainee_profile(profile: TraineeProfile, data: dict) -> TraineeProfile:
    """Validate active skill selection at the write boundary as well as in forms."""
    skills = list(data.get("skills", profile.skills.all()))
    ids = {skill.pk for skill in skills}
    if selectable_skills().filter(pk__in=ids).count() != len(ids):
        raise ValidationError("Select skills from active subjects only.")
    _save_fields(profile, data, TRAINEE_FIELDS)
    profile.skills.set(skills)
    return profile


@transaction.atomic
def update_trainer_profile(profile: TrainerProfile, data: dict) -> TrainerProfile:
    """Keep account ownership outside editable trainer details."""
    return _save_fields(profile, data, TRAINER_FIELDS)


@transaction.atomic
def save_child(record: Any, data: dict) -> Any:
    """Apply the same validated allowlist to child creation and editing."""
    return _save_fields(record, data, CHILD_FIELDS[type(record)])


@transaction.atomic
def delete_child(record: Any) -> None:
    """Remove supporting evidence from storage after its row is committed away."""
    file = getattr(record, "file", None)
    record.delete()
    if file:
        transaction.on_commit(partial(file.storage.delete, file.name))


@transaction.atomic
def update_account(user: User, data: dict) -> User:
    """Normalize account email while preserving all authorization fields."""
    allowed = {field: data[field] for field in ACCOUNT_FIELDS}
    allowed["email"] = allowed["email"].strip().lower()
    for field, value in allowed.items():
        setattr(user, field, value)
    user.full_clean()
    user.save()
    return user
