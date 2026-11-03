"""Scale the line-load meters using the existing aggregate rows."""

from django import template

from apps.dashboards.dataclasses import LineLoad

register = template.Library()


@register.filter
def line_meter_max(rows: tuple[LineLoad, ...]) -> int:
    """Keep an all-zero meter range valid without changing displayed counts."""
    return max((row.enrollments for row in rows), default=0) or 1
