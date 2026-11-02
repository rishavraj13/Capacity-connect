"""Build immutable station maps with a fixed four-query populated-data cost."""

from django.db.models import Prefetch, QuerySet

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.catalog.models import Skill
from apps.courses.constants import (
    INTERCHANGE_SUBJECT_COUNT,
    EnrollmentStatus,
    StationState,
)
from apps.courses.dataclasses import Line, Station
from apps.courses.models import Enrollment, Module


def _map_enrollments(trainee: User) -> QuerySet[Enrollment]:
    """Prefetch every dependency before computing any station state."""
    skills = Skill.objects.select_related("subject")
    modules = Module.objects.prefetch_related(Prefetch("skills", queryset=skills))
    return (
        Enrollment.objects.filter(
            trainee=trainee,
            status__in=(EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED),
        )
        .select_related("course__subject")
        .prefetch_related(Prefetch("course__modules", queryset=modules), "progress")
        .order_by("course_id")
    )


def _station(module: Module, enrollment: Enrollment, state: StationState) -> Station:
    """Detach station metadata and interchange state from prefetched ORM rows."""
    interchange = (
        len({skill.subject_id for skill in module.skills.all()})
        >= INTERCHANGE_SUBJECT_COUNT
    )
    return Station(
        module.pk,
        module.title,
        module.order,
        enrollment.course_id,
        enrollment.course.title,
        state,
        interchange,
    )


def _stations(enrollment: Enrollment) -> tuple[Station, ...]:
    """Compute sequential state independently for each enrollment."""
    done = {progress.module_id for progress in enrollment.progress.all()}
    completed = enrollment.status == EnrollmentStatus.COMPLETED
    current_seen = False
    stations = []
    for module in enrollment.course.modules.all():
        state = StationState.DONE
        if not completed and module.pk not in done:
            state = StationState.LOCKED if current_seen else StationState.CURRENT
            current_seen = True
        stations.append(_station(module, enrollment, state))
    return tuple(stations)


def station_map_for(trainee: User) -> tuple[Line, ...]:
    """Group active/completed enrollment stations without lazy ORM dependencies."""
    if (
        not trainee.is_active
        or not trainee.is_approved
        or trainee.role != UserRole.TRAINEE
    ):
        return ()
    lines = {}
    for enrollment in _map_enrollments(trainee):
        subject = enrollment.course.subject
        name, stations = lines.setdefault(subject.pk, (subject.name, []))
        stations.extend(_stations(enrollment))
    return tuple(
        Line(pk, name, tuple(stations))
        for pk, (name, stations) in sorted(lines.items())
    )
