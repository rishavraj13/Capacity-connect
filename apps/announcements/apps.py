"""Register manually authored public notices without startup queries."""

from django.apps import AppConfig


class AnnouncementsConfig(AppConfig):
    """Keep publication flows inside one application boundary."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.announcements"
