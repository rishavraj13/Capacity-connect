"""Provide one patchable business clock for assessment boundaries."""

from datetime import date, datetime

from django.utils import timezone


def now() -> datetime:
    """Keep assessment timing deterministic without a time-freezing dependency."""
    return timezone.now()


def today() -> date:
    """Use the configured local timezone for certificate dates and year sequences."""
    return timezone.localdate(now())
