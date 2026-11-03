"""Pin hardened settings and explicit reverse-proxy trust defaults."""

import os
import subprocess
import sys

from django.conf import settings


def test_shared_cookie_and_proxy_defaults() -> None:
    """Keep secure-cookie policy and proxy spoofing controls explicit."""
    assert settings.SESSION_COOKIE_AGE == 43200
    assert settings.SESSION_COOKIE_HTTPONLY and settings.CSRF_COOKIE_HTTPONLY
    assert settings.SESSION_COOKIE_SAMESITE == settings.CSRF_COOKIE_SAMESITE == "Lax"
    assert (
        not settings.USE_X_FORWARDED_PROTO and settings.SECURE_PROXY_SSL_HEADER is None
    )
    assert settings.TRUSTED_PROXY_COUNT == 0


def test_admin_path_is_environment_configurable() -> None:
    """Resolve the mounted admin path in a fresh settings process."""
    code = (
        "import django;django.setup();from django.urls import reverse;"
        'print(reverse("admin:index"))'
    )
    env = dict(
        os.environ,
        ADMIN_URL="control-centre/",
        DJANGO_SETTINGS_MODULE="config.settings.test",
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and result.stdout.strip() == "/control-centre/"
