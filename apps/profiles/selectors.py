"""Filter private objects before views can reveal their existence."""

from django.db.models import QuerySet

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.profiles.models import (
    ExternalCertificate,
    TraineeProfile,
    TrainerProfile,
)


def visible_trainees(actor: User) -> QuerySet[TraineeProfile]:
    """Return only owner or administrator visible trainee history."""
    profiles = TraineeProfile.objects.select_related("user").prefetch_related(
        "skills__subject", "qualifications", "work_experiences", "external_certificates"
    )
    if not actor.is_active or not actor.is_approved:
        return profiles.none()
    return profiles if actor.role == UserRole.ADMIN else profiles.filter(user=actor)


def visible_trainers(actor: User) -> QuerySet[TrainerProfile]:
    """Publish trainer details only within the approved portal."""
    profiles = TrainerProfile.objects.select_related("user")
    return profiles if actor.is_active and actor.is_approved else profiles.none()


def owned_children(actor: User, model: type) -> QuerySet:
    """Make cross-account edits and deletes indistinguishable from missing IDs."""
    return model.objects.filter(profile__user=actor).select_related("profile__user")


def visible_certificates(actor: User) -> QuerySet[ExternalCertificate]:
    """Apply trainee visibility before opening supporting evidence."""
    return ExternalCertificate.objects.filter(
        profile__in=visible_trainees(actor)
    ).select_related("profile__user")


def own_trainee(actor: User) -> QuerySet[TraineeProfile]:
    """Separate write ownership from administrator read visibility."""
    return TraineeProfile.objects.filter(user=actor)


def own_trainer(actor: User) -> QuerySet[TrainerProfile]:
    """Prevent trainer writes to other published profiles."""
    return TrainerProfile.objects.filter(user=actor)
