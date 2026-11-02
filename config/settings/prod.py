"""Production settings module with secure defaults enforced."""

import environ
from django.core.exceptions import ImproperlyConfigured

from config.settings.base import *  # noqa: F403
from config.settings.base import env

ALLOWED_HOSTS: list[str] = environ.Env().list("ALLOWED_HOSTS")

DEBUG: bool = False
SECRET_KEY: str = env("SECRET_KEY")

SECURE_SSL_REDIRECT: bool = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE: bool = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE: bool = env.bool("CSRF_COOKIE_SECURE", default=True)
SECURE_HSTS_SECONDS: int = env.int("SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)

SITE_BASE_URL: str = env("SITE_BASE_URL")

SECURE_HSTS_PRELOAD: bool = env.bool("SECURE_HSTS_PRELOAD", default=False)
CACHE_TABLE: str = env("CACHE_TABLE", default="capacity_connect_cache")
CACHES = {"default": env.cache_url("CACHE_URL", default=f"dbcache://{CACHE_TABLE}")}
CACHES["default"]["LOCATION"] = CACHE_TABLE
if CACHES["default"]["BACKEND"] != "django.core.cache.backends.db.DatabaseCache":
    raise ImproperlyConfigured("CACHE_URL must use the dbcache:// backend.")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{asctime} {levelname} {name} {message}", "style": "{"}
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"}
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
