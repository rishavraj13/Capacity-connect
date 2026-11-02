"""Check private delivery edge cases without exposing storage URLs."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    TraineeProfileFactory,
)

pytestmark = pytest.mark.django_db


def test_unknown_kind_and_empty_photo_return_404(client: Client) -> None:
    """Treat absent or unsupported private files as missing objects."""
    profile = TraineeProfileFactory()
    client.force_login(profile.user)
    for kind in ("unknown", "trainee"):
        assert (
            client.get(
                reverse("profiles:private_file", args=[kind, profile.pk])
            ).status_code
            == 404
        )


def test_missing_storage_object_returns_404(client: Client) -> None:
    """Avoid leaking storage errors for evidence removed outside the application."""
    certificate = ExternalCertificateFactory()
    client.force_login(certificate.profile.user)
    certificate.file.storage.delete(certificate.file.name)
    response = client.get(
        reverse("profiles:private_file", args=["certificate", certificate.pk])
    )
    assert response.status_code == 404


def test_certificate_download_headers_and_bytes(client: Client) -> None:
    """Deliver documents with a safe opaque attachment name and correct media type."""
    certificate = ExternalCertificateFactory()
    client.force_login(certificate.profile.user)
    response = client.get(
        reverse("profiles:private_file", args=["certificate", certificate.pk])
    )
    assert response["Content-Type"] == "application/pdf"
    assert ".pdf" in response["Content-Disposition"]
    assert b"".join(response.streaming_content).startswith(b"%PDF-")


def test_private_storage_has_no_public_url() -> None:
    """Prevent accidental template use of a private file's public media URL."""
    certificate = ExternalCertificateFactory()
    with pytest.raises(ValueError, match="Private files"):
        _ = certificate.file.url


def test_public_media_route_does_not_exist(client: Client) -> None:
    """Reject guessed public paths even for otherwise valid stored evidence."""
    certificate = ExternalCertificateFactory()
    assert client.get("/media/" + certificate.file.name).status_code == 404


def test_existing_photo_can_be_cleared_without_public_url(
    client: Client,
    django_capture_on_commit_callbacks: object,
) -> None:
    """Keep private upload edit widgets functional after disabling storage URLs."""
    from apps.profiles.tests.factories import TrainerProfileFactory, photo_upload

    profile = TrainerProfileFactory(photo=photo_upload())
    old = profile.photo.name
    client.force_login(profile.user)
    response = client.get(reverse("profiles:trainer_edit"))
    assert response.status_code == 200
    assert b"/media/" not in response.content
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("profiles:trainer_edit"),
            {"years_experience": 0, "photo-clear": "on"},
        )
    assert response.status_code == 302
    profile.refresh_from_db()
    assert not profile.photo and not profile.photo.storage.exists(old)
