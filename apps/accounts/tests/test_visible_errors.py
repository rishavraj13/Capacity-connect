"""Verify form-level authentication errors reach users without prior flash messages."""

import pytest
from django.urls import reverse

from apps.accounts.constants import MSG_AWAITING_APPROVAL, MSG_INVALID_CREDENTIALS
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "correct,expected",
    [(True, MSG_AWAITING_APPROVAL), (False, MSG_INVALID_CREDENTIALS)],
)
def test_fresh_login_client_renders_form_level_error(
    client: object, correct: bool, expected: str
) -> None:
    """Show approval only after correct credentials, with no signup message fallback."""
    user = UserFactory(pending_trainee=True, password="ValidPassword123!")
    response = client.post(
        reverse("login"),
        {
            "username": user.username,
            "password": "ValidPassword123!" if correct else "wrong",
        },
    )
    assert response.status_code == 200
    assert expected.encode() in response.content


def test_signup_renders_password_mismatch(client: object) -> None:
    """Make a form-wide registration refusal visible outside individual field errors."""
    response = client.post(
        reverse("signup"),
        {
            "username": "mismatch",
            "email": "mismatch@example.org",
            "role": "TRAINEE",
            "password": "ValidPassword123!",
            "confirm_password": "DifferentPassword456!",
        },
    )
    assert response.status_code == 200 and b"Passwords do not match" in response.content
