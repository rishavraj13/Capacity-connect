"""Custom user manager ensuring role and approval constraints."""

from typing import Any

from django.contrib.auth.models import UserManager as BaseUserManager

from apps.accounts.constants import UserRole


class UserManager(BaseUserManager):
    """Manager enforcing email requirement and superuser defaults."""

    def create_user(
        self,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> Any:
        """Create and save a regular user with verified email."""
        if not email:
            raise ValueError("The email field is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", UserRole.TRAINEE)
        extra_fields.setdefault("is_approved", False)
        return super().create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

    def create_superuser(
        self,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> Any:
        """Create and save a superuser enforcing ADMIN role and approval."""
        if not email:
            raise ValueError("Superusers must have an email address.")
        extra_fields["role"] = UserRole.ADMIN
        extra_fields["is_approved"] = True
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )
