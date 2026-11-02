"""Verify profile lifecycle, allowlists and transaction-aware file cleanup."""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.constants import UserRole
from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory
from apps.profiles import services
from apps.profiles.models import Qualification, TraineeProfile, TrainerProfile
from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    TraineeProfileFactory,
    TrainerProfileFactory,
    pdf_upload,
    photo_upload,
)

pytestmark = pytest.mark.django_db


def test_lazy_profiles_are_idempotent_and_preserve_role_history() -> None:
    """Retain prior role data while creating the new role profile on demand."""
    user = UserFactory(approved_trainee=True)
    trainee = services.ensure_trainee_profile(user)
    assert services.ensure_trainee_profile(user) == trainee
    user.role = UserRole.TRAINER
    user.save()
    trainer = services.ensure_trainer_profile(user)
    assert services.ensure_trainer_profile(user) == trainer
    assert TraineeProfile.objects.filter(pk=trainee.pk).exists()
    with pytest.raises(ValidationError):
        services.ensure_trainee_profile(user)
    user.role = UserRole.ADMIN
    with pytest.raises(ValidationError):
        services.ensure_trainer_profile(user)
    assert TrainerProfile.objects.count() == 1


def test_trainee_skills_and_mass_assignment() -> None:
    """Validate active skills independently of form filtering and ignore owners."""
    profile = TraineeProfileFactory()
    owner = profile.user
    skill = SkillFactory()
    services.update_trainee_profile(
        profile, {"bio": "Learner", "skills": [skill], "user": UserFactory()}
    )
    assert profile.user == owner and list(profile.skills.all()) == [skill]
    services.update_trainee_profile(profile, {"interests": "Science"})
    skill.subject.is_active = False
    skill.subject.save()
    services.update_trainee_profile(profile, {"skills": [skill]})
    assert list(profile.skills.all()) == [skill]


def test_photo_replacement_and_clear_cleanup(
    django_capture_on_commit_callbacks: object,
) -> None:
    """Delete replaced photos only once their database transaction commits."""
    profile = TraineeProfileFactory()
    services.update_trainee_profile(profile, {"photo": photo_upload()})
    original = profile.photo.name
    with django_capture_on_commit_callbacks(execute=True):
        services.update_trainee_profile(profile, {"photo": photo_upload()})
    assert not profile.photo.storage.exists(original)
    replaced = profile.photo.name
    with django_capture_on_commit_callbacks(execute=True):
        services.update_trainee_profile(profile, {"photo": False})
    assert not profile.photo.storage.exists(replaced)


def test_trainer_update_and_photo_cleanup(
    django_capture_on_commit_callbacks: object,
) -> None:
    """Apply trainer validation and the same private photo cleanup contract."""
    profile = TrainerProfileFactory()
    services.update_trainer_profile(
        profile,
        {"headline": "Teacher", "years_experience": 60, "photo": photo_upload()},
    )
    old = profile.photo.name
    with django_capture_on_commit_callbacks(execute=True):
        services.update_trainer_profile(profile, {"photo": photo_upload()})
    assert not profile.photo.storage.exists(old)
    with pytest.raises(ValidationError):
        services.update_trainer_profile(profile, {"years_experience": 61})


def test_child_save_delete_and_certificate_cleanup(
    django_capture_on_commit_callbacks: object,
) -> None:
    """Cover create, update, delete and replacement through the service layer."""
    profile = TraineeProfileFactory()
    record = services.save_child(
        Qualification(profile=profile),
        {"degree": "BSc", "institution": "University", "year": 2020},
    )
    services.save_child(record, {"degree": "MSc", "profile": TraineeProfileFactory()})
    assert record.profile == profile and record.degree == "MSc"
    services.delete_child(record)
    certificate = ExternalCertificateFactory(profile=profile)
    old = certificate.file.name
    with django_capture_on_commit_callbacks(execute=True):
        services.save_child(certificate, {"file": pdf_upload()})
    assert not certificate.file.storage.exists(old)
    current = certificate.file.name
    with django_capture_on_commit_callbacks(execute=True):
        services.delete_child(certificate)
    assert not certificate.file.storage.exists(current)


def test_account_update_normalizes_and_preserves_privileges() -> None:
    """Keep account edits from bypassing email or authorization constraints."""
    user = UserFactory(approved_trainee=True)
    services.update_account(
        user,
        {
            "first_name": "A",
            "last_name": "B",
            "email": " MIXED@Example.COM ",
            "role": UserRole.ADMIN,
            "is_staff": True,
        },
    )
    user.refresh_from_db()
    assert user.email == "mixed@example.com"
    assert user.role == UserRole.TRAINEE and not user.is_staff
    other = UserFactory()
    with pytest.raises(ValidationError):
        services.update_account(
            user, {"first_name": "A", "last_name": "B", "email": other.email.upper()}
        )


def test_rollback_preserves_old_file(
    django_capture_on_commit_callbacks: object,
) -> None:
    """Do not delete old evidence when a later part of a transaction fails."""
    certificate = ExternalCertificateFactory()
    old = certificate.file.name
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(ValidationError), transaction.atomic():
            services.save_child(certificate, {"file": pdf_upload()})
            raise ValidationError("rollback")
    assert certificate.file.storage.exists(old)
