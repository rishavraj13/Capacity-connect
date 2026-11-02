"""Prove public verification privacy and private attachment delivery."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.certificates import selectors
from apps.certificates.tests.factories import CertificateFactory

pytestmark = pytest.mark.django_db


def test_public_verification_is_minimal_and_has_privacy_headers(client: object) -> None:
    """Allow anonymous lookup without exposing email, score or grade."""
    row = CertificateFactory(enrollment__trainee__first_name="PublicName")
    response = client.get(reverse("certificates:verify", args=[row.certificate_id]))
    assert response.status_code == 200 and b"PublicName" in response.content
    assert row.enrollment.trainee.email.encode() not in response.content
    assert b"85.00" not in response.content and b"Grade" not in response.content
    assert (
        response["X-Robots-Tag"] == "noindex"
        and response["Referrer-Policy"] == "no-referrer"
    )
    assert response.context["record"].certificate_id == row.certificate_id


def test_unknown_and_malformed_ids_share_404_body(client: object) -> None:
    """Keep invalid lookup outcomes identical and safe methods only."""
    first = client.get(reverse("certificates:verify", args=["CC-2026-99999"]))
    second = client.get(reverse("certificates:verify", args=["not-an-id"]))
    assert (
        first.status_code == second.status_code == 404
        and first.content == second.content
    )
    assert first["X-Robots-Tag"] == second["X-Robots-Tag"] == "noindex"
    assert client.post(reverse("certificates:verify", args=["bad"])).status_code == 405


def test_public_form_get_redirects_to_identifier(client: object) -> None:
    """Submit the lookup through GET while keeping malformed input on the form."""
    url = reverse("certificates:verify_form")
    assert client.get(url).status_code == 200
    assert client.get(url, {"certificate_id": "bad"}).context["form"].errors
    response = client.get(url, {"certificate_id": "CC-2026-00001"})
    assert response.status_code == 302 and response["Referrer-Policy"] == "no-referrer"


def test_download_is_private_pdf_attachment_and_owner_only(client: object) -> None:
    """Authorize before storage access and never trust a caller-provided MIME type."""
    row = CertificateFactory()
    url = reverse("certificates:download", args=[row.pk])
    for user in (
        row.enrollment.trainee,
        row.enrollment.course.trainer,
        UserFactory(active_admin=True),
    ):
        client.force_login(user)
        response = client.get(url)
        assert_attachment(response, row.certificate_id)
    for user in (
        UserFactory(approved_trainee=True),
        UserFactory(approved_trainer=True),
    ):
        client.force_login(user)
        assert client.get(url).status_code == 404
    client.logout()
    assert client.get(url).status_code == 302


def test_unapproved_certificate_selector_is_empty() -> None:
    """Keep selector use outside views from bypassing approval."""
    assert not selectors.visible_certificates(
        UserFactory(pending_trainee=True)
    ).exists()


def assert_attachment(response: object, identifier: str) -> None:
    """Assert the response contract before releasing its streaming file handle."""
    assert response.status_code == 200 and response["Content-Type"] == "application/pdf"
    assert response["Cache-Control"] == "private, no-store"
    assert response["Content-Disposition"] == f'attachment; filename="{identifier}.pdf"'
    response.close()


def test_staff_participants_link_to_authorized_certificate_download(
    client: object,
) -> None:
    """Make the authorized staff download reachable from the managed course flow."""
    row = CertificateFactory()
    course = row.enrollment.course
    for user in (course.trainer, UserFactory(active_admin=True)):
        client.force_login(user)
        response = client.get(reverse("courses:participants", args=[course.pk]))
        assert (
            reverse("certificates:download", args=[row.pk]).encode() in response.content
        )
