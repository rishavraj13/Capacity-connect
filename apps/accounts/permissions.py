"""Role-based authorization mixins and decorators for view access control."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse


class RoleRequiredMixin(AccessMixin):
    """View mixin enforcing user authentication, approval, and assigned roles."""

    allowed_roles: tuple[str, ...] = ()

    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """Evaluate credentials and role permissions before dispatching view."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_active or not getattr(
            request.user, "is_approved", False
        ):
            raise PermissionDenied("Account is not active or approved.")
        if getattr(request.user, "role", None) not in self.allowed_roles:
            raise PermissionDenied("Access forbidden for assigned user role.")
        return super().dispatch(request, *args, **kwargs)


def role_required(*allowed_roles: str) -> Callable:
    """Decorator restricting view access to approved users with declared roles."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped(
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
        ) -> HttpResponse:
            """Inspect authentication, approval, and role before view execution."""
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url="login")
            if not request.user.is_active or not getattr(
                request.user, "is_approved", False
            ):
                raise PermissionDenied("Account is not active or approved.")
            if getattr(request.user, "role", None) not in allowed_roles:
                raise PermissionDenied("Access forbidden for assigned user role.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
