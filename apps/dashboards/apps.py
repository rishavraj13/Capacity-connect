"""Register read-only analytical handoffs without startup queries."""

from django.apps import AppConfig


class DashboardsConfig(AppConfig):
    """Keep analytical reads separate from domain write services."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboards"
