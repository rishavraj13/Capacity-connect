"""Keep Django admin on the same anti-abuse boundary as portal authentication."""

import logging

from django.contrib.admin import AdminSite
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator

from apps.accounts.admin_auth import RateLimitedAdminForm
from apps.accounts.constants import UserRole
from apps.core.rate_views import Kind, throttled


class CapacityAdminSite(AdminSite):
    """Use Django's normal registry and staff authorization with throttled login."""

    login_form = RateLimitedAdminForm

    @method_decorator(throttled(Kind.LOGIN))
    def login(
        self, request: HttpRequest, extra_context: dict | None = None
    ) -> HttpResponse:
        """Check failure counters before Django binds the staff login form."""
        return super().login(request, extra_context)

    def has_permission(self, request: HttpRequest) -> bool:
        """Recheck approval and Admin role for existing authenticated sessions."""
        allowed = (
            super().has_permission(request)
            and request.user.is_approved
            and request.user.role == UserRole.ADMIN
        )
        if request.user.is_authenticated and not allowed:
            logging.getLogger("security.permissions").warning(
                "permission_denied reason=admin_role_or_approval"
            )
        return allowed
