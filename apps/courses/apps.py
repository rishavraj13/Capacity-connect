"""Register course and enrollment boundaries."""

from django.apps import AppConfig


class CoursesConfig(AppConfig):
    """Keep learning workflow models discoverable by Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.courses"
