"""Factory Boy definitions for user accounts."""

from typing import Any

import factory
from factory.django import DjangoModelFactory

from apps.accounts.constants import UserRole
from apps.accounts.models import User


class UserFactory(DjangoModelFactory):
    """Factory producing valid User instances for testing."""

    class Meta:
        """Factory configuration metadata."""

        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    role = UserRole.TRAINEE
    is_approved = False
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _create(
        cls,
        model_class: type[User],
        *args: Any,
        **kwargs: Any,
    ) -> User:
        """Create a user instance with configured test password."""
        password = kwargs.pop("password", "TestPassword123!")
        user = super()._create(model_class, *args, **kwargs)
        user.set_password(password)
        user.save(update_fields=["password"])
        return user
