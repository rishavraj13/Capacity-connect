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
    ("certificate", "card", 3),
)
HEX_COLOR = re.compile(r"#(?:[a-f0-9]{3,8})\b|\b(?:rgb|hsl)a?\(", re.I)


def theme_colors(theme: str) -> dict:
    """Read the common tokens and overlay the selected theme's declarations."""
    css = TOKENS.read_text(encoding="utf-8")
    common = re.search(r":root\s*\{([^}]+)\}", css)[1]
    block = re.search(rf'\[data-theme="{theme}"\]\s*\{{([^}}]+)\}}', css)[1]
    return dict(re.findall(r"--([\w-]+):\s*(#[a-f0-9]{6});", common + block))


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
    dark, light = sorted((luminance(colors[first]), luminance(colors[second])))
    return (light + 0.05) / (dark + 0.05)


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize(("first", "second", "threshold"), PAIRS)
def test_theme_contrast(theme: str, first: str, second: str, threshold: float) -> None:
    """Require the minimum ratio for each theme's text and graphical accents."""
    ratio = contrast(theme_colors(theme), first, second)
    assert ratio >= threshold, (theme, first, second, ratio)


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
