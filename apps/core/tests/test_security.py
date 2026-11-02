"""Check public/authenticated headers and context-free production error surfaces."""

import pytest
from django.urls import reverse

from apps.accounts.forms import SignupForm
from apps.accounts.tests.factories import UserFactory
from apps.core.constants import CERTIFICATE_NAME_HELP
from apps.profiles.forms import AccountForm

pytestmark = pytest.mark.django_db


def test_security_headers_on_public_and_authenticated_pages(
    client: object, settings: object
) -> None:
    """Apply one CSP and safe shared headers to both access surfaces."""
    responses = [client.get("/")]
    client.force_login(UserFactory(approved_trainee=True))
    responses.append(client.get(reverse("trainee_home")))
    for response in responses:
        assert response["X-Frame-Options"] == "DENY"
        assert response["Referrer-Policy"] == "same-origin"
        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["Content-Security-Policy"] == settings.CONTENT_SECURITY_POLICY


def test_bare_403_and_404_and_old_admin_path_with_debug_false(
    client: object, settings: object
) -> None:
    """Render errors without application navigation, models or user context."""
    settings.DEBUG = False
    client.force_login(UserFactory(approved_trainee=True))
    response = client.get(reverse("dashboards:admin"))
    assert response.status_code == 403 and b"403 Forbidden" in response.content
    assert b"Main Navigation" not in response.content
    for url in ("/definitely-missing/", "/admin/"):
        response = client.get(url)
        assert response.status_code == 404 and b"404 Not found" in response.content


def test_permission_denial_is_logged_without_sensitive_data(
    client: object, caplog: object
) -> None:
    """Log generic security events without echoing request credentials."""
    client.force_login(UserFactory(approved_trainee=True))
    assert (
        client.get(
            reverse("dashboards:admin"), {"password": "private-marker"}
        ).status_code
        == 403
    )
    assert "permission_denied" in caplog.text and "private-marker" not in caplog.text


def test_name_help_text_does_not_reject_non_latin_names() -> None:
    """Warn about PDF rendering while preserving inclusive account input."""
    for form in (SignupForm(), AccountForm()):
        for name in ("first_name", "last_name"):
            assert form.fields[name].help_text == CERTIFICATE_NAME_HELP
            assert form.fields[name].clean("अनन्या") == "अनन्या"
