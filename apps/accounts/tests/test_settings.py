"""Tests verifying test environment settings configuration."""

from os import environ

from django.conf import settings


def test_settings_load_under_test_settings() -> None:
    """Verify test settings load correctly with in-memory DB and MD5 hasher."""
    expected_hasher: str = "django.contrib.auth.hashers.MD5PasswordHasher"
    assert environ["DJANGO_SETTINGS_MODULE"] == "config.settings.test"
    assert "memory" in settings.DATABASES["default"]["NAME"]
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert expected_hasher in settings.PASSWORD_HASHERS
    assert settings.TIME_ZONE == "Asia/Kolkata"
    assert settings.USE_TZ is True


def test_production_requires_allowed_hosts() -> None:
    """Prevent inherited development hosts from silently configuring production."""
    import os
    import subprocess
    import sys

    code = (
        "from unittest.mock import patch; "
        "from importlib import import_module; "
        "guard = patch('environ.Env.read_env'); guard.start(); "
        "import_module('config.settings.prod')"
    )
    environment = dict(os.environ, SECRET_KEY="isolated-settings-test-key")
    environment.pop("ALLOWED_HOSTS", None)
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Set the ALLOWED_HOSTS environment variable" in result.stderr


def test_production_csrf_cookie_is_httponly(monkeypatch: object) -> None:
    """Keep both production authentication cookies inaccessible to scripts."""
    from importlib import import_module

    monkeypatch.setenv("ALLOWED_HOSTS", "prod.example")
    prod = import_module("config.settings.prod")
    assert prod.CSRF_COOKIE_HTTPONLY is True


def test_csrf_cookie_is_httponly_in_shared_settings() -> None:
    """Keep server-rendered form cookie protection consistent across environments."""
    assert settings.CSRF_COOKIE_HTTPONLY is True
