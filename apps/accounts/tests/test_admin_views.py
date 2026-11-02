"""Integration tests for view controllers, admin actions, CSRF, and pagination."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.constants import (
    ADMIN_USER_PAGE_SIZE,
    UserRole,
)
from apps.accounts.tests.factories import UserFactory


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
@pytest.mark.parametrize(
    "url_name, has_arg",
    [
        ("logout", False),
        ("admin_approve_user", True),
        ("admin_reject_user", True),
        ("admin_change_role", True),
    ],
)
def test_state_changing_get_rejected_with_405(
    client: Client,
    url_name: str,
    has_arg: bool,
) -> None:
    """Verify state-changing endpoints reject GET with 405 Method Not Allowed."""
    admin = UserFactory(active_admin=True)
    target = UserFactory(pending_trainee=True)
    client.force_login(admin)
    url = reverse(url_name, args=[target.id]) if has_arg else reverse(url_name)
    assert client.get(url).status_code == 405


@pytest.mark.django_db
def test_invalid_role_post_keeps_existing_role(client: Client) -> None:
    """Reject an invalid role choice without invoking a privileged write."""
    admin = UserFactory(active_admin=True)
    target = UserFactory(approved_trainee=True)
    client.force_login(admin)
    response = client.post(
        reverse("admin_change_role", args=[target.pk]), {"role": "INVALID"}
    )
    assert response.status_code == 302
    target.refresh_from_db()
    assert target.role == UserRole.TRAINEE
