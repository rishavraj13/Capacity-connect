"""Expose pure station geometry to the shared map component."""

from django import template

from apps.courses.presentation import station_layout

register = template.Library()
register.filter("station_layout", station_layout)


@register.filter
def station_at(stations: dict, module_id: int) -> object:
    """Look up a detached station without reaching the database."""
    return stations.get(module_id) if stations else None
