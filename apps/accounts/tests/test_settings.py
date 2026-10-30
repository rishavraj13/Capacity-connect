"""Tests verifying test environment settings configuration."""

from django.conf import settings


def test_settings_load_under_test_settings() -> None:
    """Verify test settings load correctly with in-memory DB and MD5 hasher."""
    expected_hasher: str = "django.contrib.auth.hashers.MD5PasswordHasher"
    assert settings.SETTINGS_MODULE == "config.settings.test"
    assert "memory" in settings.DATABASES["default"]["NAME"]
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert expected_hasher in settings.PASSWORD_HASHERS
    assert settings.TIME_ZONE == "Asia/Kolkata"
    assert settings.USE_TZ is True
