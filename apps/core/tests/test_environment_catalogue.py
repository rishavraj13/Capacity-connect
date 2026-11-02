"""Keep documented deployment inputs aligned with actual settings reads."""

import ast
import os
import subprocess
import sys
from pathlib import Path


def environment_names() -> set[str]:
    """Inspect direct django-environ reads without importing production settings."""
    names = set()
    for path in Path("config/settings").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func = node.func
            direct = isinstance(func, ast.Name) and func.id == "env"
            method = isinstance(func, ast.Attribute) and func.attr in {
                "bool",
                "int",
                "list",
                "db",
                "cache_url",
            }
            if (direct or method) and isinstance(node.args[0], ast.Constant):
                names.add(node.args[0].value)
    return names


def test_environment_example_and_documentation_match_settings() -> None:
    """Prevent undocumented settings and stale example-only switches."""
    example = Path(".env.example").read_text(encoding="utf-8")
    names = {line.split("=", 1)[0] for line in example.splitlines() if "=" in line}
    assert names == environment_names()
    documentation = Path("docs/DEPLOYMENT.md").read_text(encoding="utf-8")
    assert all(f"`{name}`" in documentation for name in names)


def test_production_defaults_and_opt_in_proxy() -> None:
    """Pin production safety independently of the development environment file."""
    code = (
        "from config.settings import prod as s;assert s.DEBUG is False;"
        "assert s.SECURE_PROXY_SSL_HEADER == ('HTTP_X_FORWARDED_PROTO','https');"
        "assert s.CACHES['default']['LOCATION']=='review_cache';"
        "assert s.CSRF_COOKIE_HTTPONLY and s.SESSION_COOKIE_HTTPONLY"
    )
    env = dict(
        os.environ,
        SECRET_KEY="test-only-key",
        ALLOWED_HOSTS="localhost",
        SITE_BASE_URL="https://example.org",
        USE_X_FORWARDED_PROTO="True",
        CACHE_TABLE="review_cache",
        DEBUG="True",
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
