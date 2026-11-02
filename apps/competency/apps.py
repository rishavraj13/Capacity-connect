"""Register trainer declarations without startup queries."""

from django.apps import AppConfig


class CompetencyConfig(AppConfig):
    """Keep competency models inside their own domain boundary."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.competency"
