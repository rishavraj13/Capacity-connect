"""Exercise public presentation without changing selectors or form validation."""

from datetime import UTC, datetime

import pytest
from django.urls import reverse

from apps.accounts.constants import (
    MSG_ACCOUNT_DISABLED,
    MSG_AWAITING_APPROVAL,
    MSG_INVALID_CREDENTIALS,
)
from apps.accounts.tests.factories import UserFactory
from apps.announcements.tests.factories import AnnouncementFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.core.constants import CERTIFICATE_NAME_HELP
from apps.core.tests.frontend_markup import assert_accessible_shell

pytestmark = pytest.mark.django_db
PASSWORD = "ValidPassword123!"


def public_html(response: object, status: int = 200) -> str:
    """Require an accessible shell for the actual public response."""
    assert response.status_code == status
    html = response.content.decode("utf-8")
    assert_accessible_shell(html)
    return html


def test_home_uses_published_board_order_and_escapes_body(client: object) -> None:
    """Render all categories, preserve selector order and hide drafts."""
    cases = (
        ("NOTICE", "NOTICE", "Signal orientation"),
        ("ACHIEVEMENT", "ACHIEVED", "Workshop complete"),
        ("NEW_CONTENT", "NEW", "New workbook"),
        ("DEADLINE", "DEADLINE", "Friday deadline"),
    )
    for category, _, title in reversed(cases):
        AnnouncementFactory(
            published=True,
            category=category,
            title=title,
            published_at=datetime(2026, 11, 3, 9, tzinfo=UTC),
            body="<script>alert(1)</script>\nBring a notebook.",
        )
    AnnouncementFactory(title="Unpublished signal rehearsal")
    html = public_html(client.get(reverse("announcements:home")))
    assert "<h1>Every skill has a route. Find yours.</h1>" in html
    assert 'class="metro-illustration" aria-hidden="true"' in html
    assert "Unpublished signal rehearsal" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;<br>" in html
    assert all(f">{label}</" in html for _, label, _ in cases)
    positions = [html.index(title) for _, _, title in cases]
    assert positions == sorted(positions)


def test_empty_home_has_single_board_empty_state(client: object) -> None:
    """Keep an empty public board readable and offer both entry actions."""
    html = public_html(client.get(reverse("announcements:home")))
    assert html.count("No announcements yet.") == 1
    assert f'href="{reverse("login")}">Log in<' in html
    assert f'href="{reverse("signup")}">Sign up<' in html
    assert "How it works" in html


@pytest.mark.parametrize(
    ("trait", "landing"),
    [
        ("approved_trainee", "trainee_home"),
        ("approved_trainer", "trainer_home"),
        ("active_admin", "admin_panel"),
    ],
)
def test_signed_in_home_uses_role_landing(
    client: object, trait: str, landing: str
) -> None:
    """Use the existing role landing context for the public hero action."""
    client.force_login(UserFactory(**{trait: True}))
    html = public_html(client.get(reverse("announcements:home")))
    assert f'href="{reverse(landing)}">Go to your dashboard<' in html


@pytest.mark.parametrize(
    "case",
    [
        ("pending_trainee", PASSWORD, MSG_AWAITING_APPROVAL, "Notice"),
        ("pending_trainee", "incorrect", MSG_INVALID_CREDENTIALS, "Error"),
        ("rejected_user", PASSWORD, MSG_ACCOUNT_DISABLED, "Error"),
    ],
    ids=("pending", "invalid", "disabled"),
)
def test_login_shows_each_disclosure_once(client: object, case: tuple) -> None:
    """Keep the backend disclosure in a single visible text alert."""
    trait, password, message, label = case
    user = UserFactory(password=PASSWORD, **{trait: True})
    html = public_html(
        client.post(
            reverse("login"),
            {
                "username": user.username,
                "password": password,
                "next": "/courses/",
            },
        )
    )
    assert html.count(message) == 1
    assert 'role="alert"' in html and f"<strong>{label}</strong>" in html
    assert 'name="next" value="/courses/"' in html
    assert reverse("certificates:verify_form") in html


def test_login_field_errors_link_to_controls(client: object) -> None:
    """Associate required-field errors with the inputs and summary links."""
    html = public_html(client.post(reverse("login"), {}))
    for name in ("username", "password"):
        assert f'href="#id_{name}"' in html
        assert f'aria-describedby="id_{name}_error"' in html
    assert html.count('aria-invalid="true"') == 2


def test_signup_displays_role_cards_help_and_bound_errors(client: object) -> None:
    """Keep posted role choices, labels and guidance available without JS."""
    html = public_html(client.post(reverse("signup"), {"role": "TRAINER"}))
    assert "<legend>Role</legend>" in html
    assert html.count('name="role"') == 2 and html.count('type="radio"') == 2
    assert 'value="TRAINER" checked' in html and 'value="TRAINEE"' in html
    assert html.count(CERTIFICATE_NAME_HELP) == 2
    assert "at least eight characters" in html
    assert (
        'href="#id_username"' in html and 'aria-describedby="id_username_error"' in html
    )


def test_signup_notice_is_visible_on_login(client: object) -> None:
    """Keep the existing approval flash visible after a valid signup."""
    html = public_html(
        client.post(
            reverse("signup"),
            {
                "username": "newtrainee",
                "email": "fresh@example.org",
                "role": "TRAINEE",
                "password": PASSWORD,
                "confirm_password": PASSWORD,
            },
            follow=True,
        )
    )
    assert html.count(MSG_AWAITING_APPROVAL) == 1
    assert "Portal Login" in html


def test_verify_form_hint_does_not_add_a_client_pattern(client: object) -> None:
    """Show the ID format while leaving malformed input to server validation."""
    response = client.get(reverse("certificates:verify_form"))
    html = public_html(response)
    assert "CC-YYYY-NNNNN" in html and 'aria-describedby="certificate-id-hint' in html
    assert " pattern=" not in html
    assert response["X-Robots-Tag"] == "noindex"
    assert response["Referrer-Policy"] == "no-referrer"


def test_verify_result_limits_fields_and_preserves_headers(client: object) -> None:
    """Present only the approved public certificate fields and verification mark."""
    row = CertificateFactory(enrollment__trainee__first_name="PublicName")
    response = client.get(reverse("certificates:verify", args=[row.certificate_id]))
    html = public_html(response)
    assert "Valid certificate" in html and 'aria-label="Verified"' in html
    assert row.certificate_id in html and "PublicName" in html
    assert row.enrollment.course.title in html and "Issued" in html
    assert row.enrollment.trainee.email not in html
    assert all(private not in html for private in ("85.00", "Grade", "Score"))
    assert response["X-Robots-Tag"] == "noindex"
    assert response["Referrer-Policy"] == "no-referrer"


def test_verify_not_found_is_identical_for_invalid_and_unknown(client: object) -> None:
    """Use the same standalone error layout for both missing-record outcomes."""
    responses = [
        client.get(reverse("certificates:verify", args=[identifier]))
        for identifier in ("bad-id", "CC-2026-99999")
    ]
    first, second = (public_html(response, 404) for response in responses)
    assert first == second and "Certificate not found" in first
    assert all(response["X-Robots-Tag"] == "noindex" for response in responses)
    assert all(response["Referrer-Policy"] == "no-referrer" for response in responses)
