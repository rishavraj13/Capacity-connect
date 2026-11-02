"""Patch the one shared clock for deterministic publication tests."""

import pytest

from apps.assessments.tests.factories import MOMENT
from apps.core import clock


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch: object) -> None:
    """Keep announcement transitions independent of the execution time."""
    monkeypatch.setattr(clock, "now", lambda: MOMENT)
