"""Integration tests for view controllers, admin actions, CSRF, and pagination."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.constants import (
    ADMIN_USER_PAGE_SIZE,
    UserRole,
)
from apps.accounts.models import User
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
def test_admin_approve_and_reject_actions(client: Client) -> None:
    """Verify administrator can approve and reject target user accounts."""
    admin_user = UserFactory(active_admin=True)
    UserFactory(active_admin=True)
    target = UserFactory(pending_trainee=True)
    client.force_login(admin_user)

    approve_url = reverse("admin_approve_user", args=[target.id])
    assert client.get(approve_url).status_code == 405
    client.post(approve_url)
    target.refresh_from_db()
    assert target.is_approved is True

    reject_url = reverse("admin_reject_user", args=[target.id])
    assert client.get(reject_url).status_code == 405
    client.post(reject_url)
    target.refresh_from_db()
    assert target.is_active is False


@pytest.mark.django_db
def test_admin_change_role_action(client: Client) -> None:
    """Verify administrator can change target user roles via POST submission."""
    admin_user = UserFactory(active_admin=True)
    target = UserFactory(approved_trainee=True)
    client.force_login(admin_user)
    url = reverse("admin_change_role", args=[target.id])
    assert client.get(url).status_code == 405
    client.post(url, data={"role": UserRole.TRAINER})
    target.refresh_from_db()
    assert target.role == UserRole.TRAINER


@pytest.mark.django_db
def test_admin_self_rejection_blocked_in_view(client: Client) -> None:
    """Verify administrator attempting self-rejection receives feedback message."""
    admin_user = UserFactory(active_admin=True)
    UserFactory(active_admin=True)
    client.force_login(admin_user)
    response = client.post(
        reverse("admin_reject_user", args=[admin_user.id]),
        follow=True,
    )
    assert response.status_code == 200
    admin_user.refresh_from_db()
    assert admin_user.is_active is True


@pytest.mark.django_db
def test_admin_last_admin_demotion_blocked_in_view(client: Client) -> None:
    """Verify demoting the sole active admin is blocked in view layer."""
    sole_admin = UserFactory(active_admin=True)
    client.force_login(sole_admin)
    response = client.post(
        reverse("admin_change_role", args=[sole_admin.id]),
        data={"role": UserRole.TRAINEE},
        follow=True,
    )
    assert response.status_code == 200
    sole_admin.refresh_from_db()
    assert sole_admin.role == UserRole.ADMIN


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
def test_admin_user_list_query_count_and_pagination(
    client: Client,
    django_assert_num_queries,
) -> None:
    """Verify user list view pagination at 20 items with bounded database queries."""
    admin_user = UserFactory(active_admin=True)
    UserFactory.create_batch(25, approved_trainee=True)
    client.force_login(admin_user)

    # 4 queries: 1 session, 1 authenticated user, 1 COUNT(*), 1 page slice
    with django_assert_num_queries(4):
        response_p1 = client.get(reverse("admin_user_list"))
    assert response_p1.status_code == 200
    assert len(response_p1.context["page_obj"]) == ADMIN_USER_PAGE_SIZE

    response_p2 = client.get(f"{reverse('admin_user_list')}?page=2")
    assert response_p2.status_code == 200
    # 25 trainees + 1 admin = 26 total => page 1 has 20, page 2 has 6
    assert len(response_p2.context["page_obj"]) == 6


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
