"""Check actual pages and development-only access without a browser dependency."""

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.urls import reverse

from apps.core.tests.frontend_markup import assert_accessible_shell
from apps.core.tests.test_page_queries import RECIPES


@pytest.mark.django_db
@pytest.mark.parametrize("name", RECIPES)
def test_existing_pages_render_accessible_shell(client: object, name: str) -> None:
    """Exercise populated list and detail pages using the existing role fixtures."""
    setup = RECIPES[name]()
    if setup.user:
        client.force_login(setup.user)
    response = client.get(setup.url)
    assert response.status_code == 200
    assert_accessible_shell(response.content.decode("utf-8"))


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["login", "signup", "certificates:verify_form"])
def test_public_forms_render_accessible_shell(client: object, name: str) -> None:
    """Verify the controls and links still work in the shared shell."""
    response = client.get(reverse(name))
    assert response.status_code == 200
    assert_accessible_shell(response.content.decode("utf-8"))


def test_styleguide_requires_debug(client: object, settings: object) -> None:
    """Refuse public access outside DEBUG and render sample markup in development."""
    assert client.get("/styleguide/").status_code == 404
    settings.DEBUG = True
    response = client.get("/styleguide/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Component gallery" in html and "aria-invalid" in html
    assert_accessible_shell(html)


@pytest.mark.parametrize("status", [403, 404, 429, 500])
def test_error_pages_render_without_request_or_database(status: int) -> None:
    """Retain a readable standalone heading and route home on service errors."""
    html = render_to_string(f"{status}.html")
    assert f"<h1>{status} " in html and 'href="/"' in html
    assert_accessible_shell(html)


def test_theme_controls_bootstrap_from_local_assets(client: object) -> None:
    """Require default markup and a blocking head script for first-paint selection."""
    html = client.get("/login/").content.decode("utf-8")
    assert 'data-theme="day"' in html
    assert "data-theme-control hidden" in html
    assert all(f'value="{theme}"' in html for theme in ("day", "night", "sign"))
    assert '<script src="/static/js/theme.js"></script>' in html.split("</head>")[0]
    script = (settings.BASE_DIR / "static/js/theme.js").read_text(encoding="utf-8")
    assert "localStorage.getItem" in script and "localStorage.setItem" in script
    assert "prefers-color-scheme: dark" in script


def test_local_assets_csp_and_private_path(client: object) -> None:
    """Keep the policy strict and decline guessed private upload URLs."""
    response = client.get("/login/")
    directives = response["Content-Security-Policy"]
    for directive in (
        "style-src 'self'",
        "script-src 'self'",
        "font-src 'self'",
        "img-src 'self' data:",
        "frame-ancestors 'none'",
    ):
        assert directive in directives
    assert "unsafe-inline" not in directives
    assert client.get("/private_uploads/f0-probe.pdf").status_code == 404


def test_debug_off_does_not_route_static_files(client: object) -> None:
    """Keep production asset serving outside Django and out of private storage."""
    assert finders.find("css/tokens.css")
    assert not settings.STATIC_ROOT.is_relative_to(settings.BASE_DIR)
    assert client.get("/static/css/tokens.css").status_code == 404
