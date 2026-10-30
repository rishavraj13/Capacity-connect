"""Unit tests for user registration, login authentication, and role forms."""

import pytest

from apps.accounts.constants import (
    MSG_ACCOUNT_DISABLED,
    MSG_AWAITING_APPROVAL,
    MSG_INVALID_CREDENTIALS,
    UserRole,
)
from apps.accounts.forms import LoginForm, RoleChangeForm, SignupForm
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_signup_form_valid() -> None:
    """Verify SignupForm accepts compliant registration data."""
    form = SignupForm(
        data={
            "username": "candidate_1",
            "email": "candidate1@example.com",
            "first_name": "First",
            "last_name": "Last",
            "role": UserRole.TRAINEE,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
        }
    )
    assert form.is_valid()


@pytest.mark.django_db
def test_signup_form_duplicate_email_case_insensitive() -> None:
    """Verify SignupForm rejects existing email regardless of casing."""
    UserFactory(email="existing@example.com")
    form = SignupForm(
        data={
            "username": "new_user",
            "email": "EXISTING@EXAMPLE.COM",
            "role": UserRole.TRAINEE,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
        }
    )
    assert not form.is_valid()
    assert "email" in form.errors


@pytest.mark.django_db
def test_signup_form_privileged_field_injection_ignored() -> None:
    """Verify privileged parameters submitted in POST data cannot be bound."""
    form = SignupForm(
        data={
            "username": "hacker",
            "email": "hacker@example.com",
            "role": UserRole.ADMIN,
            "is_approved": True,
            "is_staff": True,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
        }
    )
    assert not form.is_valid()
    assert "role" in form.errors


@pytest.mark.django_db
def test_login_form_unapproved_user_gives_awaiting_approval() -> None:
    """Verify unapproved user with correct password gets awaiting approval error."""
    password: str = "CorrectPassword123!"
    UserFactory(username="pending_usr", pending_trainee=True, password=password)
    form = LoginForm(data={"username": "pending_usr", "password": password})
    assert not form.is_valid()
    assert MSG_AWAITING_APPROVAL in form.errors["__all__"]


@pytest.mark.django_db
def test_login_form_wrong_password_gives_generic_message() -> None:
    """Verify wrong password returns generic error without status leaks."""
    UserFactory(
        username="some_usr",
        pending_trainee=True,
        password="RightPassword123!",
    )
    form = LoginForm(data={"username": "some_usr", "password": "WrongPassword"})
    assert not form.is_valid()
    assert MSG_INVALID_CREDENTIALS in form.errors["__all__"]


@pytest.mark.django_db
def test_login_form_unknown_user_gives_generic_message() -> None:
    """Verify nonexistent user returns generic error matching wrong password output."""
    form = LoginForm(data={"username": "ghost_user", "password": "AnyPassword123!"})
    assert not form.is_valid()
    assert MSG_INVALID_CREDENTIALS in form.errors["__all__"]


@pytest.mark.django_db
def test_login_form_inactive_user_gives_disabled_message() -> None:
    """Verify rejected or disabled account receives account disabled message."""
    password: str = "GoodPassword123!"
    UserFactory(username="banned_usr", rejected_user=True, password=password)
    form = LoginForm(data={"username": "banned_usr", "password": password})
    assert not form.is_valid()
    assert MSG_ACCOUNT_DISABLED in form.errors["__all__"]


@pytest.mark.django_db
def test_login_form_approved_user_succeeds() -> None:
    """Verify approved user with correct credentials validates successfully."""
    password: str = "GoodPassword123!"
    UserFactory(username="active_usr", approved_trainee=True, password=password)
    form = LoginForm(data={"username": "active_usr", "password": password})
    assert form.is_valid()


def test_role_change_form_validation() -> None:
    """Verify RoleChangeForm accepts valid roles and rejects unrecognized options."""
    assert RoleChangeForm(data={"role": UserRole.TRAINER}).is_valid()
    assert not RoleChangeForm(data={"role": "INVALID"}).is_valid()


@pytest.mark.django_db
def test_signup_form_duplicate_username_rejected() -> None:
    """Verify signup rejects duplicate username case-insensitively."""
    UserFactory(username="ExistingUser")
    form = SignupForm(
        data={
            "username": "existinguser",
            "email": "fresh@example.com",
            "first_name": "New",
            "last_name": "Person",
            "role": UserRole.TRAINEE,
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
        }
    )
    assert not form.is_valid()
    assert "username" in form.errors


@pytest.mark.django_db
def test_signup_form_password_mismatch_rejected() -> None:
    """Verify signup rejects mismatched password confirmation."""
    form = SignupForm(
        data={
            "username": "newperson",
            "email": "person@example.com",
            "first_name": "New",
            "last_name": "Person",
            "role": UserRole.TRAINEE,
            "password": "ValidPassword123!",
            "confirm_password": "MismatchingPass123!",
        }
    )
    assert not form.is_valid()
    assert "__all__" in form.errors


def test_login_form_empty_credentials() -> None:
    """Verify login form handles empty username or password cleanly."""
    form = LoginForm(data={"username": "", "password": ""})
    assert not form.is_valid()
