"""Register protected completion records without startup queries."""

from django.apps import AppConfig


class CertificatesConfig(AppConfig):
    """Keep certificate records isolated from completion orchestration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.certificates"
