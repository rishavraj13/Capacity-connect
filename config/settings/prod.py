"""Production settings module with secure defaults enforced."""

from config.settings.base import *  # noqa: F403
from config.settings.base import env

DEBUG: bool = False
SECRET_KEY: str = env("SECRET_KEY")

SECURE_SSL_REDIRECT: bool = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE: bool = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE: bool = env.bool("CSRF_COOKIE_SECURE", default=True)
SECURE_HSTS_SECONDS: int = env.int("SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
SECURE_CONTENT_TYPE_NOSNIFF: bool = env.bool(
    "SECURE_CONTENT_TYPE_NOSNIFF", default=True
)
