"""Register catalog boundaries for reusable subject and skill records."""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Keep catalog models discoverable by Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
