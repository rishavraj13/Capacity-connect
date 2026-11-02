"""Select the standard custom-site hook without replacing the admin registry."""

from django.contrib.admin.apps import AdminConfig


class CapacityAdminConfig(AdminConfig):
    """Preserve built-in admin models/URLs while choosing the hardened site."""

    default_site = "config.admin_site.CapacityAdminSite"
