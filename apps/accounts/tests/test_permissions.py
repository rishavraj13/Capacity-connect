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
from apps.core.tests.matrix import MatrixRequest, assert_matrix_case, matrix_id

PERMISSION_MATRIX: list[tuple[str, str, str, int]] = [
    ("anonymous", "trainee_home", "GET", 302),
    ("approved_trainee", "trainee_home", "GET", 200),
    ("approved_trainer", "trainee_home", "GET", 403),
    ("approved_admin", "trainee_home", "GET", 403),
    ("unapproved_user", "trainee_home", "GET", 403),
    ("rejected_user", "trainee_home", "GET", 302),
    ("anonymous", "trainer_home", "GET", 302),
    ("approved_trainee", "trainer_home", "GET", 403),
    ("approved_trainer", "trainer_home", "GET", 200),
    ("approved_admin", "trainer_home", "GET", 403),
    ("unapproved_user", "trainer_home", "GET", 403),
    ("rejected_user", "trainer_home", "GET", 302),
    ("anonymous", "admin_panel", "GET", 302),
    ("approved_trainee", "admin_panel", "GET", 403),
    ("approved_trainer", "admin_panel", "GET", 403),
    ("approved_admin", "admin_panel", "GET", 200),
    ("unapproved_user", "admin_panel", "GET", 403),
    ("rejected_user", "admin_panel", "GET", 302),
    ("anonymous", "admin_user_list", "GET", 302),
    ("approved_trainee", "admin_user_list", "GET", 403),
    ("approved_trainer", "admin_user_list", "GET", 403),
    ("approved_admin", "admin_user_list", "GET", 200),
    ("unapproved_user", "admin_user_list", "GET", 403),
    ("rejected_user", "admin_user_list", "GET", 302),
    ("anonymous", "admin_pending_list", "GET", 302),
    ("approved_trainee", "admin_pending_list", "GET", 403),
    ("approved_trainer", "admin_pending_list", "GET", 403),
    ("approved_admin", "admin_pending_list", "GET", 200),
    ("unapproved_user", "admin_pending_list", "GET", 403),
    ("rejected_user", "admin_pending_list", "GET", 302),
    ("anonymous", "admin_approve_user", "POST", 302),
    ("approved_trainee", "admin_approve_user", "POST", 403),
    ("approved_trainer", "admin_approve_user", "POST", 403),
    ("approved_admin", "admin_approve_user", "POST", 302),
    ("unapproved_user", "admin_approve_user", "POST", 403),
    ("rejected_user", "admin_approve_user", "POST", 302),
    ("anonymous", "admin_reject_user", "POST", 302),
    ("approved_trainee", "admin_reject_user", "POST", 403),
    ("approved_trainer", "admin_reject_user", "POST", 403),
    ("approved_admin", "admin_reject_user", "POST", 302),
    ("unapproved_user", "admin_reject_user", "POST", 403),
    ("rejected_user", "admin_reject_user", "POST", 302),
    ("anonymous", "admin_change_role", "POST", 302),
    ("approved_trainee", "admin_change_role", "POST", 403),
    ("approved_trainer", "admin_change_role", "POST", 403),
    ("approved_admin", "admin_change_role", "POST", 302),
    ("unapproved_user", "admin_change_role", "POST", 403),
    ("rejected_user", "admin_change_role", "POST", 302),
    ("anonymous", "logout", "POST", 302),
    ("approved_trainee", "logout", "POST", 302),
    ("approved_trainer", "logout", "POST", 302),
    ("approved_admin", "logout", "POST", 302),
    ("unapproved_user", "logout", "POST", 302),
    ("rejected_user", "logout", "POST", 302),
]


@pytest.mark.django_db
@pytest.mark.parametrize("matrix_entry", PERMISSION_MATRIX, ids=matrix_id)
def test_permission_matrix(client: Client, matrix_entry: tuple) -> None:
    """Preserve the approved B1 permission contract through shared machinery."""
    target = UserFactory(pending_trainee=True)
    UserFactory(active_admin=True)
    _, name, _, _ = matrix_entry
    state_urls = {"admin_approve_user", "admin_reject_user", "admin_change_role"}
    url = reverse(name, args=[target.id] if name in state_urls else [])
    data = {"role": UserRole.TRAINER} if name == "admin_change_role" else {}
    assert_matrix_case(client, matrix_entry, MatrixRequest(url, data))


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
