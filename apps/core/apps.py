"""Core application configuration module."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Application configuration for shared core models and utilities."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.core"
    label: str = "core"
