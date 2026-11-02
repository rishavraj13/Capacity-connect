"""Exercise complete role-specific profile workflows through real forms."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory
from apps.profiles.models import ExternalCertificate, Qualification, WorkExperience
from apps.profiles.tests.factories import (
    TraineeProfileFactory,
    TrainerProfileFactory,
    pdf_upload,
    photo_upload,
)

pytestmark = pytest.mark.django_db


def test_trainee_profile_post_and_private_photo(client: Client) -> None:
    """Persist actual uploaded bytes and selected skills through the owner form."""
    profile = TraineeProfileFactory()
    skill = SkillFactory()
    client.force_login(profile.user)
    response = client.post(
        reverse("profiles:trainee_edit"),
        {
            "bio": "Learner",
            "interests": "Science",
            "skills": [skill.pk],
            "photo": photo_upload(),
            "user": UserFactory().pk,
        },
    )
    assert response.status_code == 302
    profile.refresh_from_db()
    assert profile.bio == "Learner" and list(profile.skills.all()) == [skill]
    response = client.get(
        reverse("profiles:private_file", args=["trainee", profile.pk])
    )
    assert response["Content-Type"] == "image/png"
    assert response["Content-Disposition"].startswith("attachment;")
    assert b"".join(response.streaming_content).startswith(b"\x89PNG")


def test_trainer_profile_post(client: Client) -> None:
    """Keep trainer and account details independently editable with normalized email."""
    profile = TrainerProfileFactory()
    client.force_login(profile.user)
    response = client.post(
        reverse("profiles:trainer_edit"),
        {
            "bio": "Teacher",
            "headline": "Trainer",
            "years_experience": 12,
            "photo": photo_upload(),
            "is_superuser": True,
        },
    )
    assert response.status_code == 302
    profile.refresh_from_db()
    assert profile.years_experience == 12 and profile.headline == "Trainer"


@pytest.mark.parametrize("role", ["TRAINEE", "TRAINER", "ADMIN"])
def test_account_post_preserves_privileges(client: Client, role: str) -> None:
    """Accept basic account changes through Django's lazy request user."""
    user = UserFactory(role=role, is_approved=True)
    client.force_login(user)
    response = client.post(
        reverse("profiles:account_edit"),
        {
            "first_name": "First",
            "last_name": "Last",
            "email": "NEW@EXAMPLE.COM",
            "role": "ADMIN",
            "is_staff": True,
        },
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.email == "new@example.com"
    assert user.role == role and not user.is_staff


CHILD_CASES = [
    (
        "qualification",
        Qualification,
        {"degree": "BSc", "institution": "College", "year": 2020},
        "degree",
    ),
    (
        "experience",
        WorkExperience,
        {
            "organisation": "Company",
            "role": "Analyst",
            "start_date": "2020-01-01",
            "description": "Work",
        },
        "organisation",
    ),
    (
        "certificate",
        ExternalCertificate,
        {"title": "Award", "issuer": "College", "issued_on": "2020-01-01"},
        "title",
    ),
]


@pytest.mark.parametrize(
    "case", CHILD_CASES, ids=["qualification", "experience", "certificate"]
)
def test_child_create_edit_delete(client: Client, case: tuple) -> None:
    """Prove every child workflow assigns ownership and changes persisted data."""
    slug, model, original, field = case
    profile = TraineeProfileFactory()
    client.force_login(profile.user)
    data = dict(original, profile=TraineeProfileFactory().pk)
    if slug == "certificate":
        data["file"] = pdf_upload()
    assert client.post(reverse(f"profiles:{slug}_create"), data).status_code == 302
    record = model.objects.get(profile=profile)
    data = dict(original, **{field: "Updated"})
    assert (
        client.post(
            reverse(f"profiles:{slug}_edit", args=[record.pk]), data
        ).status_code
        == 302
    )
    record.refresh_from_db()
    assert getattr(record, field) == "Updated"
    assert (
        client.post(reverse(f"profiles:{slug}_delete", args=[record.pk])).status_code
        == 302
    )
    assert not model.objects.filter(pk=record.pk).exists()


def test_invalid_upload_never_persists(client: Client) -> None:
    """Keep content-spoofed images out of storage through the HTTP form path."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    profile = TraineeProfileFactory()
    client.force_login(profile.user)
    response = client.post(
        reverse("profiles:trainee_edit"),
        {"bio": "Attempt", "photo": SimpleUploadedFile("spoof.png", b"plain text")},
    )
    assert response.status_code == 200
    assert "photo" in response.context["form"].errors
    profile.refresh_from_db()
    assert not profile.photo and profile.bio == ""
