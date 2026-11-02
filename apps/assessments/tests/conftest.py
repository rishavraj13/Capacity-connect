"""Patch only the single assessment business clock for deterministic tests."""

from typing import Any

import pytest

from apps.assessments.tests.factories import MOMENT


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch: Any) -> None:
    """Keep business-time boundaries independent of wall-clock test duration."""
    monkeypatch.setattr("apps.core.clock.now", lambda: MOMENT)
