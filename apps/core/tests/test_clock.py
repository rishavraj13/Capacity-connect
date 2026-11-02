"""Keep production time behind one timezone-aware clock boundary."""

from datetime import datetime

from django.utils.timezone import is_aware

from apps.core import clock


def test_now_returns_aware_datetime() -> None:
    """Avoid accidental naive timestamps in services that use the shared clock."""
    instant = clock.now()
    assert isinstance(instant, datetime) and is_aware(instant)
