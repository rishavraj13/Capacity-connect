"""Prevent cross-owner disclosure and mutation through guessed record IDs."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    QualificationFactory,
    TraineeProfileFactory,
    WorkExperienceFactory,
    photo_upload,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("actor", ["trainee", "trainer"])
def test_other_trainee_history_and_files_are_hidden(client: Client, actor: str) -> None:
    """Return 404 for private profile and file requests outside visibility."""
    profile = TraineeProfileFactory(photo=photo_upload())
    certificate = ExternalCertificateFactory(profile=profile)
    user = UserFactory(**{f"approved_{actor}": True})
    client.force_login(user)
    urls = [
        reverse("profiles:trainee_detail", args=[profile.pk]),
        reverse("profiles:private_file", args=["trainee", profile.pk]),
        reverse("profiles:private_file", args=["certificate", certificate.pk]),
    ]
    for url in urls:
        assert client.get(url).status_code == 404


@pytest.mark.parametrize(
    "slug,factory",
    [
        ("qualification", QualificationFactory),
        ("experience", WorkExperienceFactory),
        ("certificate", ExternalCertificateFactory),
    ],
)
@pytest.mark.parametrize(
    "operation", [("edit", "get"), ("edit", "post"), ("delete", "post")]
)
def test_child_idor_returns_404(
    client: Client, slug: str, factory: type, operation: tuple
) -> None:
    """Deny another trainee's child objects before processing attacker input."""
    action, method = operation
    record = factory()
    client.force_login(UserFactory(approved_trainee=True))
    url = reverse(f"profiles:{slug}_{action}", args=[record.pk])
    assert getattr(client, method)(url).status_code == 404
    assert type(record).objects.filter(pk=record.pk).exists()
