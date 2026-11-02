"""Register feedback without startup queries."""

from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    """Keep feedback inside its own application boundary."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.feedback"
