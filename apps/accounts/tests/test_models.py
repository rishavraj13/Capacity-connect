"""Tests for custom User model attributes, managers, and constraints."""

import pytest
from django.db import IntegrityError

from apps.accounts.constants import UserRole
from apps.accounts.factories import UserFactory
from apps.accounts.models import User


@pytest.mark.django_db
def test_user_defaults() -> None:
    """Verify newly created users default to unapproved and a valid role."""
    user = UserFactory()
    assert user.is_approved is False
    assert user.role == UserRole.TRAINEE
    assert user.role in UserRole.values


@pytest.mark.django_db
def test_email_uniqueness_enforced() -> None:
    """Verify creating duplicate email addresses raises an IntegrityError."""
    duplicate_email: str = "duplicate@example.com"
    UserFactory(email=duplicate_email)
    with pytest.raises(IntegrityError):
        UserFactory(email=duplicate_email)


@pytest.mark.django_db
def test_create_superuser_gives_admin_and_approved() -> None:
    """Verify create_superuser unconditionally sets ADMIN role and approved flag."""
    superuser = User.objects.create_superuser(
        username="admin_user",
        email="admin@example.com",
        password="SuperSecretPassword123!",
    )
    assert superuser.role == UserRole.ADMIN
    assert superuser.is_approved is True
    assert superuser.is_staff is True
    assert superuser.is_superuser is True


@pytest.mark.django_db
def test_create_user_without_email_raises_value_error() -> None:
    """Verify creating user without email raises ValueError."""
    with pytest.raises(ValueError, match="The email field is required."):
        User.objects.create_user(
            username="no_email_user",
            email="",
            password="Password123!",
        )


@pytest.mark.django_db
def test_create_superuser_without_email_raises_value_error() -> None:
    """Verify creating superuser without email raises ValueError."""
    with pytest.raises(ValueError, match="Superusers must have an email address."):
        User.objects.create_superuser(
            username="no_email_admin",
            email="",
            password="Password123!",
        )


@pytest.mark.django_db
def test_create_user_success() -> None:
    """Verify create_user succeeds with valid credentials and sets trainee role."""
    user = User.objects.create_user(
        username="trainee_user",
        email="trainee@example.com",
        password="ValidPassword123!",
    )
    assert user.role == UserRole.TRAINEE
    assert user.is_approved is False
    assert str(user) == "trainee_user (trainee@example.com)"
