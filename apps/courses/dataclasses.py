"""Define immutable station-map handoff data without ORM behavior."""

from dataclasses import dataclass

from apps.courses.constants import StationState


@dataclass(frozen=True, slots=True)
class Station:
    """Keep presentation code independent of enrollment queries."""

    module_id: int
    title: str
    order: int
    course_id: int
    course_title: str
    state: StationState
    is_interchange: bool


@dataclass(frozen=True, slots=True)
class Line:
    """Group stations by subject for the later Metro frontend."""

    subject_id: int
    subject_name: str
    stations: tuple[Station, ...]
