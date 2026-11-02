"""Require portal approval/Admin role as well as Django's staff flag."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("change", [{"is_approved": False}, {"role": "TRAINER"}])
def test_unapproved_or_demoted_staff_cannot_authenticate_or_open_admin(
    client: object, change: dict
) -> None:
    """Close a staff-flag bypass of the portal's approval and role boundaries."""
    user = UserFactory(active_admin=True)
    for name, value in change.items():
        setattr(user, name, value)
    user.save()
    response = client.post(
        reverse("admin:login"),
        {"username": user.username, "password": "TestPassword123!"},
    )
    assert response.status_code == 200 and response.context["form"].errors
    client.force_login(user)
    assert client.get(reverse("admin:index")).status_code == 302


def test_approved_admin_login_still_works(client: object) -> None:
    """Preserve Django's normal valid staff login and pair reset path."""
    user = UserFactory(active_admin=True)
    response = client.post(
        reverse("admin:login"),
        {"username": user.username, "password": "TestPassword123!"},
    )
    assert response.status_code == 302
    assert client.get(reverse("admin:index")).status_code == 200
