"""Unit tests for user domain services and administrative protection rules."""

import pytest

from apps.accounts.constants import UserRole
from apps.accounts.services import (
    approve_user,
    change_role,
    register_user,
    reject_user,
)
from apps.accounts.tests.factories import UserFactory
from apps.core.exceptions import (
    InvalidRoleError,
    LastAdminProtectionError,
    SelfModificationError,
)


@pytest.mark.django_db
def test_register_user_creates_unapproved_trainee() -> None:
    """Verify registration defaults to unapproved with normalized email."""
    data = {
        "username": "new_trainee",
        "email": "TRAINEE_NEW@EXAMPLE.COM",
        "password": "SecurePassword123!",
        "first_name": "New",
        "last_name": "Trainee",
        "role": UserRole.TRAINEE,
    }
    user = register_user(data)
    assert user.is_approved is False
    assert user.role == UserRole.TRAINEE
    assert user.email == "trainee_new@example.com"


@pytest.mark.django_db
def test_register_user_invalid_role_raises_error() -> None:
    """Verify signup attempting ADMIN role raises InvalidRoleError."""
    data = {
        "username": "bad_admin",
        "email": "bad@example.com",
        "password": "SecurePassword123!",
        "role": UserRole.ADMIN,
    }
    with pytest.raises(InvalidRoleError):
        register_user(data)


@pytest.mark.django_db
def test_approve_user() -> None:
    """Verify approving a user sets is_approved flag to True."""
    admin_user = UserFactory(active_admin=True)
    pending = UserFactory(pending_trainee=True)
    approved = approve_user(pending, admin_user)
    assert approved.is_approved is True


@pytest.mark.django_db
def test_reject_user_deactivates_account() -> None:
    """Verify rejecting user sets is_active and is_approved to False."""
    admin1 = UserFactory(active_admin=True)
    UserFactory(active_admin=True)
    target = UserFactory(approved_trainee=True)
    rejected = reject_user(target, admin1)
    assert rejected.is_active is False
    assert rejected.is_approved is False


@pytest.mark.django_db
def test_admin_cannot_reject_self() -> None:
    """Verify administrator self-rejection raises SelfModificationError."""
    admin_user = UserFactory(active_admin=True)
    UserFactory(active_admin=True)
    with pytest.raises(SelfModificationError):
        reject_user(admin_user, admin_user)


@pytest.mark.django_db
def test_last_admin_cannot_be_rejected() -> None:
    """Verify rejecting the sole active admin raises LastAdminProtectionError."""
    sole_admin = UserFactory(active_admin=True)
    staff_caller = UserFactory(role=UserRole.TRAINER, is_approved=True)
    with pytest.raises(LastAdminProtectionError):
        reject_user(sole_admin, staff_caller)


@pytest.mark.django_db
def test_change_role_success() -> None:
    """Verify updating a user role succeeds for valid transitions."""
    admin_user = UserFactory(active_admin=True)
    trainee = UserFactory(approved_trainee=True)
    updated = change_role(trainee, UserRole.TRAINER, admin_user)
    assert updated.role == UserRole.TRAINER


@pytest.mark.django_db
def test_admin_cannot_demote_self() -> None:
    """Verify administrator self-demotion raises SelfModificationError."""
    admin_user = UserFactory(active_admin=True)
    UserFactory(active_admin=True)
    with pytest.raises(SelfModificationError):
        change_role(admin_user, UserRole.TRAINEE, admin_user)


@pytest.mark.django_db
def test_last_admin_cannot_be_demoted() -> None:
    """Verify demoting the sole active admin raises LastAdminProtectionError."""
    sole_admin = UserFactory(active_admin=True)
    staff_caller = UserFactory(role=UserRole.TRAINER, is_approved=True)
    with pytest.raises(LastAdminProtectionError):
        change_role(sole_admin, UserRole.TRAINEE, staff_caller)


@pytest.mark.django_db
def test_change_role_invalid_role_raises_error() -> None:
    """Verify invalid role string raises InvalidRoleError."""
    admin_user = UserFactory(active_admin=True)
    trainee = UserFactory(approved_trainee=True)
    with pytest.raises(InvalidRoleError):
        change_role(trainee, "INVALID_ROLE", admin_user)


@pytest.mark.django_db
def test_reject_admin_when_another_active_admin_remains() -> None:
    """Permit administrative rejection when portal administration survives."""
    actor = UserFactory(active_admin=True)
    target = UserFactory(active_admin=True)
    reject_user(target, actor)
    assert not target.is_active
