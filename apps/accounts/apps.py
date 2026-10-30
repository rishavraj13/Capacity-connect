"""Accounts application configuration module."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for user authentication and accounts app."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.accounts"
    label: str = "accounts"
