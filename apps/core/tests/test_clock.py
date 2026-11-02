"""Keep production time behind one timezone-aware clock boundary."""

from datetime import datetime

from django.utils.timezone import is_aware

from apps.core import clock


def test_now_returns_aware_datetime() -> None:
    """Avoid accidental naive timestamps in services that use the shared clock."""
    instant = clock.now()
    assert isinstance(instant, datetime) and is_aware(instant)


def test_today_uses_local_date(monkeypatch: object) -> None:
    """Use Kolkata's date rather than the preceding UTC date around midnight."""
    from datetime import UTC, date

    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 12, 31, 20, tzinfo=UTC))
    assert clock.today() == date(2027, 1, 1)
