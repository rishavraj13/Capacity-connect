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
    for prefix in ("/media/", "/private_uploads/"):
        assert client.get(prefix + certificate.file.name).status_code == 404


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


@pytest.mark.parametrize("kind", ["trainee", "certificate"])
def test_download_ignores_untrusted_content_type(client: Client, kind: str) -> None:
    """Choose response type from validated storage suffixes, never upload headers."""
    from apps.profiles.tests.factories import pdf_upload, photo_upload

    upload = photo_upload() if kind == "trainee" else pdf_upload()
    upload.content_type = "text/html"
    record = (
        TraineeProfileFactory(photo=upload)
        if kind == "trainee"
        else ExternalCertificateFactory(file=upload)
    )
    user = record.user if kind == "trainee" else record.profile.user
    client.force_login(user)
    response = client.get(reverse("profiles:private_file", args=[kind, record.pk]))
    assert response["Content-Type"] == (
        "image/png" if kind == "trainee" else "application/pdf"
    )
    assert response["Content-Disposition"].startswith("attachment;")
    response.close()


def test_private_storage_is_separate_from_public_roots(settings: object) -> None:
    """Keep evidence on the private filesystem root and off public media storage."""
    from pathlib import Path

    certificate = ExternalCertificateFactory()
    private = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    assert Path(certificate.file.path).is_relative_to(private)
    assert not private.is_relative_to(Path(settings.MEDIA_ROOT).resolve())
    assert not private.is_relative_to(Path(settings.STATIC_ROOT).resolve())
    assert str(private) == certificate.file.storage.location
