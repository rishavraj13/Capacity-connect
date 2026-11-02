"""Reuse portal failure counters for the built-in Admin authentication surface."""

from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError

from apps.accounts.constants import UserRole
from apps.core.rate_views import record_login_failure, reset_login_pair


class RateLimitedAdminForm(AdminAuthenticationForm):
    """Count only rejected staff credentials and reset only successful pair history."""

    def clean(self) -> dict:
        """Preserve Django's staff checks while sharing the existing limiter hooks."""
        try:
            data = super().clean()
        except ValidationError:
            record_login_failure(self.request)
            raise
        reset_login_pair(self.request)
        return data

    def confirm_login_allowed(self, user: object) -> None:
        """Keep leftover staff flags from bypassing approval or a demotion."""
        super().confirm_login_allowed(user)
        if not user.is_approved or user.role != UserRole.ADMIN:
            raise self.get_invalid_login_error()
