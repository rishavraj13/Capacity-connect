"""Form definitions for authentication, user registration, and role assignment."""

from typing import Any

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from apps.accounts.constants import (
    MSG_ACCOUNT_DISABLED,
    MSG_AWAITING_APPROVAL,
    MSG_INVALID_CREDENTIALS,
    SIGNUP_ROLES,
    UserRole,
)
from apps.accounts.models import User


class SignupForm(forms.Form):
    """Registration form collecting applicant credentials and desired role."""

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "username"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    role = forms.ChoiceField(
        choices=[(role, UserRole(role).label) for role in SIGNUP_ROLES],
        required=True,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        required=True,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        required=True,
    )

    def clean_username(self) -> str:
        """Validate username uniqueness case-insensitively."""
        username: str = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self) -> str:
        """Validate email address uniqueness case-insensitively."""
        email: str = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean(self) -> dict[str, Any]:
        """Validate matching passwords and check standard password rules."""
        cleaned_data: dict[str, Any] = super().clean()
        password: str | None = cleaned_data.get("password")
        confirm: str | None = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        if password:
            temp_user = User(
                username=cleaned_data.get("username", ""),
                email=cleaned_data.get("email", ""),
            )
            password_validation.validate_password(password, temp_user)
        return cleaned_data


class LoginForm(AuthenticationForm):
    """Authentication form verifying passwords prior to evaluation of approval."""

    def clean(self) -> dict[str, Any]:
        """Verify password first to prevent status leaks for non-existent users."""
        username: str | None = self.cleaned_data.get("username")
        password: str | None = self.cleaned_data.get("password")
        if not username or not password:
            return self.cleaned_data
        user: User | None = User.objects.filter(username__iexact=username).first()
        if user is None or not user.check_password(password):
            raise forms.ValidationError(
                MSG_INVALID_CREDENTIALS,
                code="invalid_login",
            )
        if not user.is_active:
            raise forms.ValidationError(
                MSG_ACCOUNT_DISABLED,
                code="inactive",
            )
        if not user.is_approved:
            raise forms.ValidationError(
                MSG_AWAITING_APPROVAL,
                code="unapproved",
            )
        self.user_cache = user
        return self.cleaned_data


class RoleChangeForm(forms.Form):
    """Form used by administrators to modify a user's assigned portal role."""

    role = forms.ChoiceField(
        choices=UserRole.choices,
        required=True,
    )
