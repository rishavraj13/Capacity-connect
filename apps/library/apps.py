"""Register private trainer resources."""

from django.apps import AppConfig


class LibraryConfig(AppConfig):
    """Keep resource models discoverable by Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.library"
