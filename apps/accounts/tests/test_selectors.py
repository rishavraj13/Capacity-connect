"""Unit tests for user database selectors and status filtering."""

import pytest

from apps.accounts.constants import (
    STATUS_ACTIVE,
    STATUS_ALL,
    STATUS_INACTIVE,
    STATUS_PENDING,
    UserRole,
)
from apps.accounts.selectors import pending_users, users_filtered
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_pending_users_selector() -> None:
    """Verify pending_users only retrieves active unapproved users."""
    pending = UserFactory(pending_trainee=True)
    UserFactory(approved_trainee=True)
    UserFactory(rejected_user=True)
    results = list(pending_users())
    assert results == [pending]


@pytest.mark.django_db
def test_users_filtered_by_role() -> None:
    """Verify users_filtered isolates accounts matching specified role."""
    trainee = UserFactory(approved_trainee=True)
    UserFactory(approved_trainer=True)
    results = list(users_filtered(role=UserRole.TRAINEE))
    assert results == [trainee]


@pytest.mark.django_db
def test_users_filtered_by_pending_status() -> None:
    """Verify users_filtered with pending status isolates unapproved accounts."""
    pending = UserFactory(pending_trainer=True)
    UserFactory(approved_trainer=True)
    results = list(users_filtered(status=STATUS_PENDING))
    assert results == [pending]


@pytest.mark.django_db
def test_users_filtered_by_active_and_inactive() -> None:
    """Verify users_filtered isolates active and inactive accounts correctly."""
    active = UserFactory(approved_trainee=True)
    inactive = UserFactory(rejected_user=True)
    active_results = list(users_filtered(status=STATUS_ACTIVE))
    inactive_results = list(users_filtered(status=STATUS_INACTIVE))
    assert active in active_results
    assert inactive in inactive_results
    assert active not in inactive_results


@pytest.mark.django_db
def test_users_filtered_all_returns_entire_roster() -> None:
    """Verify selecting all role and status options returns all accounts."""
    u1 = UserFactory(approved_trainee=True)
    u2 = UserFactory(rejected_user=True)
    all_results = list(users_filtered(role=STATUS_ALL, status=STATUS_ALL))
    assert u1 in all_results
    assert u2 in all_results
