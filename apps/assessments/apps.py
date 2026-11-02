"""Register assessment authoring and attempt boundaries."""

from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    """Keep assessment models discoverable without startup queries."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.assessments"
