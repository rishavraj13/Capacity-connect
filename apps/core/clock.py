"""Provide one patchable business clock for assessment boundaries."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime

from django.utils import timezone

_override: ContextVar[datetime | None] = ContextVar("capacity_clock", default=None)


def now() -> datetime:
    """Keep assessment timing deterministic without a time-freezing dependency."""
    return _override.get() or timezone.now()


def today() -> date:
    """Use the configured local timezone for certificate dates and year sequences."""
    return timezone.localdate(now())


@contextmanager
def at(instant: datetime) -> Iterator[None]:
    """Replay service workflows without changing the process-wide clock."""
    if timezone.is_naive(instant):
        raise ValueError("Clock override must be timezone-aware.")
    token = _override.set(instant)
    try:
        yield
    finally:
        _override.reset(token)
