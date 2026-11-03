"""Pin frontend file budgets and test the declared WCAG color pairs."""

import re

import pytest
from django.conf import settings

from apps.core.tests.frontend_markup import Markup

ROOT = settings.BASE_DIR
TOKENS = ROOT / "static/css/tokens.css"
THEMES = ("day", "night", "sign")
PAIRS = (
    ("ink", "paper", 4.5),
    ("ink", "card", 4.5),
    ("muted", "paper", 4.5),
    ("muted", "card", 4.5),
    ("accent", "paper", 4.5),
    ("accent", "card", 4.5),
    ("alert", "paper", 4.5),
    ("alert", "card", 4.5),
    ("success", "paper", 4.5),
    ("success", "card", 4.5),
    ("board-text", "board", 4.5),
    ("gold", "card", 3),
    ("gold-text", "card", 4.5),
    ("line-1", "paper", 3),
    ("line-1", "card", 3),
    ("line-2", "paper", 3),
    ("line-2", "card", 3),
    ("line-3", "paper", 3),
    ("line-3", "card", 3),
    ("focus", "paper", 3),
    ("focus", "card", 3),
    ("ink", "paper", 3),
    ("primary-text", "primary-fill", 4.5),
    ("secondary-text", "secondary-fill", 4.5),
    ("board-label", "board", 4.5),
    ("badge-text", "badge-fill", 4.5),
    ("success", "badge-fill", 4.5),
    ("accent", "badge-fill", 4.5),
)
HEX_COLOR = re.compile(r"#(?:[a-f0-9]{3,8})\b|\b(?:rgb|hsl)a?\(", re.I)
COLOR_TOKEN = re.compile(r"--([\w-]+):\s*(#[a-f0-9]{6}|var\(--[\w-]+\));")


def theme_colors(theme: str) -> dict:
    """Read the common tokens and overlay the selected theme's declarations."""
    css = TOKENS.read_text(encoding="utf-8")
    common = re.search(r":root\s*\{([^}]+)\}", css)[1]
    block = re.search(rf'\[data-theme="{theme}"\]\s*\{{([^}}]+)\}}', css)[1]
    return dict(COLOR_TOKEN.findall(common + block))


def color_value(colors: dict, token: str) -> str:
    """Resolve a semantic color alias against the active theme."""
    value = colors[token]
    return color_value(colors, value[6:-1]) if value.startswith("var(--") else value


def luminance(color: str) -> float:
    """Convert sRGB to relative luminance using the WCAG transfer function."""
    values = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in values
    ]
    return sum(
        value * weight
        for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
    )


def contrast(colors: dict, first: str, second: str) -> float:
    """Return the brighter-to-darker contrast ratio for a token pair."""
    dark, light = sorted(
        luminance(color_value(colors, token)) for token in (first, second)
    )
    return (light + 0.05) / (dark + 0.05)


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize(("first", "second", "threshold"), PAIRS)
def test_theme_contrast(theme: str, first: str, second: str, threshold: float) -> None:
    """Require the minimum ratio for each theme's text and graphical accents."""
    ratio = contrast(theme_colors(theme), first, second)
    assert ratio >= threshold, (theme, first, second, ratio)


def test_no_js_dark_fallback_preserves_explicit_themes() -> None:
    """Match night colors for unset themes while excluding all explicit selections."""
    css = TOKENS.read_text(encoding="utf-8")
    fallback = re.search(
        r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*"
        r":root:not\(\[data-theme\]\)\s*\{([^}]+)\}",
        css,
    )
    assert fallback, "missing attribute-free dark fallback"
    night = re.search(r'\[data-theme="night"\]\s*\{([^}]+)\}', css)[1]
    assert dict(COLOR_TOKEN.findall(fallback[1])) == dict(COLOR_TOKEN.findall(night))
    assert "color-scheme: dark;" in fallback[1]
    for theme in THEMES:
        assert f'[data-theme="{theme}"]' in css


def test_templates_have_no_inline_styles_scripts_or_handlers() -> None:
    """Check every project template for external or CSP-incompatible markup."""
    for path in (ROOT / "templates").rglob("*.html"):
        source = path.read_text(encoding="utf-8")
        assert not source.startswith("\ufeff") and len(source.splitlines()) <= 150, path
        Markup().feed(source)


def test_static_file_budgets_and_local_css() -> None:
    """Keep shipped CSS and JS small and all literal colors in the token file."""
    for path in (ROOT / "static").rglob("*"):
        if path.suffix not in {".css", ".js"}:
            continue
        source = path.read_text(encoding="utf-8")
        limit = 400 if path.suffix == ".css" else 150
        assert not source.startswith("\ufeff") and len(source.splitlines()) <= limit, (
            path
        )
        if path.suffix == ".css":
            assert not re.search(r"https?://|url\(\s*['\"]?//", source), path
            assert "!important" not in source, path
            assert path == TOKENS or not HEX_COLOR.search(source), path


def test_station_pulse_only_runs_when_motion_is_allowed() -> None:
    """Require every pulse declaration to be inside the motion opt-in."""
    css = (ROOT / "static/css/components.css").read_text(encoding="utf-8")
    allowed = re.compile(
        r"@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{\s*"
        r"\.station-halo\s*\{[^}]*animation:\s*station-pulse[^}]*\}\s*\}"
    )
    assert allowed.search(css)
    assert not re.search(
        r"animation(?:-name)?:[^;{}]*station-pulse", allowed.sub("", css)
    )


@pytest.mark.parametrize("theme", THEMES)
def test_staff_chart_contrast(theme: str) -> None:
    """Check chart graphics against their card and page surfaces."""
    colors = theme_colors(theme)
    for token in ("ink", "line-2", "line-3"):
        for surface in ("paper", "card"):
            assert contrast(colors, token, surface) >= 3
    assert contrast(colors, "accent", "card") >= 3
