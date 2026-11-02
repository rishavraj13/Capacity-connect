"""Keep new certificate timestamps deterministic through the shared clock."""

from datetime import UTC, date, datetime

import pytest

from apps.core import clock


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch: object) -> None:
    """Patch both public clock functions rather than individual callers."""
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 11, 2, 12, tzinfo=UTC))
    monkeypatch.setattr(clock, "today", lambda: date(2026, 11, 2))
