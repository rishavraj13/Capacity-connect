"""Custom user model definition for Capacity Connect."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.constants import UserRole
from apps.accounts.managers import UserManager


class User(AbstractUser):
    """Custom user model incorporating portal roles and approval state."""

    Role = UserRole

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.TRAINEE,
        help_text="Designated portal permission role for the user.",
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Designates whether this user has administrator approval.",
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        help_text="Unique primary email address for the user.",
    )

    objects = UserManager()

    REQUIRED_FIELDS: list[str] = ["email"]

    class Meta:
        """User model metadata."""

        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        """Return human-readable representation with username and email."""
        return f"{self.username} ({self.email})"
