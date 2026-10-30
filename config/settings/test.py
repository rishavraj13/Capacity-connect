"""Test environment settings with fast password hashing and in-memory database."""

from config.settings.base import *  # noqa: F403

SECRET_KEY: str = "test-secret-key-capacity-connect-suite"
DEBUG: bool = False

PASSWORD_HASHERS: list[str] = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DATABASES: dict = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

EMAIL_BACKEND: str = "django.core.mail.backends.locmem.EmailBackend"
