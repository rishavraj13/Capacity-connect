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
def test_error_pages_render_without_request_database_or_assets(
    status: int, settings: object
) -> None:
    """Retain readable error markup with unavailable static assets."""
    settings.STATIC_URL = "/unavailable-static/"
    html = render_to_string(f"{status}.html")
    assert f"<h1>{status} " in html and 'href="/"' in html
    assert_accessible_shell(html)


def test_theme_controls_bootstrap_from_local_assets(client: object) -> None:
    """Require default markup and a blocking head script for first-paint selection."""
    html = client.get("/login/").content.decode("utf-8")
    assert '<html lang="en">' in html
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
    assert directives == (
        "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; "
        "form-action 'self'; style-src 'self'; script-src 'self'; "
        "font-src 'self'; img-src 'self' data:"
    )
    assert client.get("/private_uploads/f0-probe.pdf").status_code == 404


def test_debug_off_does_not_route_static_files(client: object) -> None:
    """Keep production asset serving outside Django and out of private storage."""
    assert finders.find("css/tokens.css")
    assert not settings.STATIC_ROOT.is_relative_to(settings.BASE_DIR)
    assert client.get("/static/css/tokens.css").status_code == 404


def test_head_preloads_two_local_fonts(client: object) -> None:
    """Keep the regular body and bold heading font preloads same-origin."""
    html = client.get("/login/").content.decode("utf-8")
    head = html.split("</head>", 1)[0]
    names = (
        "inter-latin-400-normal.woff2",
        "bricolage-grotesque-latin-800-normal.woff2",
    )
    assert head.count('rel="preload"') == len(names)
    for name in names:
        assert (
            f'href="/static/fonts/{name}" as="font" type="font/woff2" crossorigin'
            in head
        )
        assert finders.find(f"fonts/{name}")


def test_main_navigation_has_keyboard_toggle_and_desktop_override(
    client: object,
) -> None:
    """Keep one set of links visible on desktop without scripting."""
    html = client.get(reverse("login")).content.decode()
    assert 'id="main-nav-toggle" type="checkbox"' in html
    assert '<label for="main-nav-toggle">' in html
    css = (settings.BASE_DIR / "static/css/components.css").read_text(encoding="utf-8")
    assert "@media (min-width: 768px)" in css
    assert ".nav-toggle:not(:checked) ~ .nav-links { display: none; }" in css
