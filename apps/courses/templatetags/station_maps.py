"""Expose pure station geometry to the shared map component."""

from collections.abc import Iterable

from django import template

from apps.catalog.models import Skill
from apps.courses.constants import INTERCHANGE_SUBJECT_COUNT
from apps.courses.presentation import station_layout

register = template.Library()
register.filter("station_layout", station_layout)


@register.filter
def station_at(stations: dict, module_id: int) -> object:
    """Look up a detached station without reaching the database."""
    return stations.get(module_id) if stations else None


@register.filter
def interchange(skills: Iterable[Skill]) -> bool:
    """Label a cross-subject station from its already-prefetched skills."""
    return len({skill.subject_id for skill in skills}) >= INTERCHANGE_SUBJECT_COUNT
