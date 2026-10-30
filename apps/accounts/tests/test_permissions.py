"""Permission matrix tests verifying access control across all roles."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.test import Client, RequestFactory
from django.urls import reverse
from django.views.generic import View

from apps.accounts.constants import UserRole
from apps.accounts.permissions import RoleRequiredMixin
from apps.accounts.tests.factories import UserFactory

PROTECTED_URLS: list[tuple[str, list[str]]] = [
    ("trainee_home", [UserRole.TRAINEE]),
    ("trainer_home", [UserRole.TRAINER]),
    ("admin_panel", [UserRole.ADMIN]),
    ("admin_user_list", [UserRole.ADMIN]),
    ("admin_pending_list", [UserRole.ADMIN]),
]


@pytest.mark.django_db
@pytest.mark.parametrize("url_name, allowed_roles", PROTECTED_URLS)
def test_anonymous_redirected_to_login(
    client: Client,
    url_name: str,
    allowed_roles: list[str],
) -> None:
    """Verify anonymous access redirects to login endpoint."""
    url: str = reverse(url_name)
    response = client.get(url)
    assert response.status_code == 302
    assert "/login/" in response.url


@pytest.mark.django_db
@pytest.mark.parametrize("url_name, allowed_roles", PROTECTED_URLS)
def test_approved_user_authorized_role_permitted(
    client: Client,
    url_name: str,
    allowed_roles: list[str],
) -> None:
    """Verify approved user with authorized role can access protected endpoint."""
    role: str = allowed_roles[0]
    user = UserFactory(role=role, is_approved=True, is_active=True)
    client.force_login(user)
    response = client.get(reverse(url_name))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("url_name, allowed_roles", PROTECTED_URLS)
def test_unapproved_user_access_forbidden(
    client: Client,
    url_name: str,
    allowed_roles: list[str],
) -> None:
    """Verify unapproved user of matching role receives 403 Forbidden."""
    role: str = allowed_roles[0]
    user = UserFactory(role=role, is_approved=False, is_active=True)
    client.force_login(user)
    response = client.get(reverse(url_name))
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("url_name, allowed_roles", PROTECTED_URLS)
def test_wrong_role_access_forbidden(
    client: Client,
    url_name: str,
    allowed_roles: list[str],
) -> None:
    """Verify approved user with unauthorized role receives 403 Forbidden."""
    forbidden_role: str = next(
        role for role in UserRole.values if role not in allowed_roles
    )
    user = UserFactory(role=forbidden_role, is_approved=True, is_active=True)
    client.force_login(user)
    response = client.get(reverse(url_name))
    assert response.status_code == 403


class DummyCBV(RoleRequiredMixin, View):
    """Test view inheriting RoleRequiredMixin for role validation."""

    allowed_roles = (UserRole.TRAINER,)

    def get(self, request: HttpRequest) -> HttpResponse:
        """Return simple 200 OK response when access is granted."""
        return HttpResponse("OK")


def test_role_required_mixin_anonymous_redirects(rf: RequestFactory) -> None:
    """Verify RoleRequiredMixin redirects unauthenticated requests."""
    request = rf.get("/dummy/")
    request.user = AnonymousUser()
    response = DummyCBV.as_view()(request)
    assert response.status_code == 302


@pytest.mark.django_db
def test_role_required_mixin_unapproved_raises_forbidden(
    rf: RequestFactory,
) -> None:
    """Verify RoleRequiredMixin raises PermissionDenied for unapproved users."""
    request = rf.get("/dummy/")
    request.user = UserFactory(role=UserRole.TRAINER, is_approved=False)
    with pytest.raises(PermissionDenied):
        DummyCBV.as_view()(request)


@pytest.mark.django_db
def test_role_required_mixin_wrong_role_raises_forbidden(
    rf: RequestFactory,
) -> None:
    """Verify RoleRequiredMixin raises PermissionDenied for incorrect role."""
    request = rf.get("/dummy/")
    request.user = UserFactory(role=UserRole.TRAINEE, is_approved=True, is_active=True)
    with pytest.raises(PermissionDenied):
        DummyCBV.as_view()(request)


@pytest.mark.django_db
def test_role_required_mixin_authorized_succeeds(rf: RequestFactory) -> None:
    """Verify RoleRequiredMixin dispatches view for authorized user."""
    request = rf.get("/dummy/")
    request.user = UserFactory(role=UserRole.TRAINER, is_approved=True, is_active=True)
    response = DummyCBV.as_view()(request)
    assert response.status_code == 200
