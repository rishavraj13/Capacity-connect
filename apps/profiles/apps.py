"""Register private learner and trainer profile records."""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """Keep profile models discoverable by Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
