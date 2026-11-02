"""Provide one patchable business clock for assessment boundaries."""

from datetime import datetime

from django.utils import timezone


def now() -> datetime:
    """Keep assessment timing deterministic without a time-freezing dependency."""
    return timezone.now()
