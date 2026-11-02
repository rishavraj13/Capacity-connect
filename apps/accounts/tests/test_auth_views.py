"""Integration tests for view controllers, admin actions, CSRF, and pagination."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.constants import (
    UserRole,
)
from apps.accounts.models import User
from apps.accounts.services import reject_user
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_signup_view_get_and_post_creates_unapproved_user(client: Client) -> None:
    """Verify signup flow accepts credentials and creates unapproved account."""
    get_res = client.get(reverse("signup"))
    assert get_res.status_code == 200
    post_data = {
        "username": "fresh_applicant",
        "email": "fresh@example.com",
        "role": UserRole.TRAINEE,
        "password": "ValidPassword123!",
        "confirm_password": "ValidPassword123!",
    }
    post_res = client.post(reverse("signup"), data=post_data)
    assert post_res.status_code == 302
    assert post_res.url == reverse("login")
    created = User.objects.get(username="fresh_applicant")
    assert created.is_approved is False


@pytest.mark.django_db
def test_login_post_redirects_to_role_landing_page(client: Client) -> None:
    """Verify successful login redirects user to their designated dashboard."""
    password = "ValidPassword123!"
    trainer = UserFactory(approved_trainer=True, password=password)
    response = client.post(
        reverse("login"),
        data={"username": trainer.username, "password": password},
    )
    assert response.status_code == 302
    assert response.url == reverse("trainer_home")


@pytest.mark.django_db
def test_logout_view_post_only(client: Client) -> None:
    """Verify logout rejects GET requests with 405 and clears session on POST."""
    user = UserFactory(approved_trainee=True)
    client.force_login(user)
    get_res = client.get(reverse("logout"))
    assert get_res.status_code == 405
    post_res = client.post(reverse("logout"))
    assert post_res.status_code == 302
    assert post_res.url == reverse("login")


@pytest.mark.django_db
def test_csrf_enforced_on_post() -> None:
    """Verify POST submissions lacking valid CSRF tokens receive 403 Forbidden."""
    enforced_client = Client(enforce_csrf_checks=True)
    response = enforced_client.post(
        reverse("signup"),
        data={"username": "bot_user"},
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_authenticated_user_redirected_from_auth_pages(client: Client) -> None:
    """Verify logged in users visiting login or signup are redirected home."""
    trainee = UserFactory(approved_trainee=True)
    client.force_login(trainee)
    assert client.get(reverse("login")).status_code == 302
    assert client.get(reverse("signup")).status_code == 302


def test_login_view_get_renders_login_template(client: Client) -> None:
    """Verify GET request to login renders the login page with 200 status."""
    response = client.get(reverse("login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_next_parameter_handling(client: Client) -> None:
    """Verify login redirects to valid internal next URL and ignores external URLs."""
    pwd = "ValidPassword123!"
    trainee = UserFactory(approved_trainee=True, password=pwd)

    # 1. Valid internal next URL
    res_valid = client.post(
        f"{reverse('login')}?next=/trainee/",
        data={"username": trainee.username, "password": pwd},
    )
    assert res_valid.status_code == 302
    assert res_valid.url == "/trainee/"

    # 2. Unsafe external next URL is ignored, fallback to role home
    res_external = client.post(
        f"{reverse('login')}?next=https://evil.com/phishing",
        data={"username": trainee.username, "password": pwd},
    )
    assert res_external.status_code == 302
    assert res_external.url == reverse("trainee_home")


@pytest.mark.django_db
def test_rejected_user_with_active_session_loses_access(client: Client) -> None:
    """Verify user deactivated while holding an active session loses access."""
    admin = UserFactory(active_admin=True)
    trainee = UserFactory(approved_trainee=True)
    client.force_login(trainee)

    assert client.get(reverse("trainee_home")).status_code == 200
    reject_user(trainee, admin)

    res = client.get(reverse("trainee_home"))
    assert res.status_code == 302
    assert reverse("login") in res.url


@pytest.mark.django_db
def test_secure_login_rejects_http_next(client: Client) -> None:
    """Keep HTTPS sessions from redirecting onto insecure transport."""
    user = UserFactory(approved_trainee=True)
    response = client.post(
        reverse("login"),
        {
            "username": user.username,
            "password": "TestPassword123!",
            "next": "http://testserver/unsafe/",
        },
        secure=True,
    )
    assert response.url == reverse("trainee_home")


@pytest.mark.django_db
def test_signup_view_posting_admin_role_rejected(client: Client) -> None:
    """Verify submitting ADMIN role or is_approved flag on signup is rejected."""
    bad_data = {
        "username": "rogue_user",
        "email": "rogue@example.com",
        "role": UserRole.ADMIN,
        "is_approved": True,
        "password": "ValidPassword123!",
        "confirm_password": "ValidPassword123!",
    }
    response = client.post(reverse("signup"), data=bad_data)
    assert response.status_code == 200
    assert not User.objects.filter(username="rogue_user").exists()
