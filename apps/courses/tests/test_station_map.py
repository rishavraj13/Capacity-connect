"""Prove every handoff state, interchange detection and bounded query cost."""

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory, SubjectFactory
from apps.courses.constants import EnrollmentStatus, StationState
from apps.courses.dataclasses import Line, Station
from apps.courses.selectors import station_map_for
from apps.courses.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)

pytestmark = pytest.mark.django_db


def _state_scenario() -> tuple:
    """Build a multi-course scenario including completed and dropped history."""
    trainee = UserFactory(approved_trainee=True)
    subject = SubjectFactory()
    course = CourseFactory(subject=subject)
    enrollment = EnrollmentFactory(trainee=trainee, course=course)
    modules = [ModuleFactory(course=course, order=order) for order in (1, 2, 3)]
    modules[1].skills.set([SkillFactory(subject=subject), SkillFactory()])
    ModuleProgressFactory(enrollment=enrollment, module=modules[0])
    completed = EnrollmentFactory(
        trainee=trainee, course__subject=subject, status=EnrollmentStatus.COMPLETED
    )
    ModuleFactory(course=completed.course, order=1)
    EnrollmentFactory(trainee=trainee, status=EnrollmentStatus.DROPPED)
    return trainee, course, completed


def test_station_map_states_grouping_order_and_interchanges() -> None:
    """Compute state per course and group multiple courses under one subject."""
    trainee, course, completed = _state_scenario()
    lines = station_map_for(trainee)
    assert len(lines) == 1 and isinstance(lines[0], Line)
    stations = lines[0].stations
    assert all(isinstance(station, Station) for station in stations)
    assert [station.state for station in stations] == [
        StationState.DONE,
        StationState.CURRENT,
        StationState.LOCKED,
        StationState.DONE,
    ]
    assert [station.is_interchange for station in stations] == [
        False,
        True,
        False,
        False,
    ]
    assert [station.course_id for station in stations] == [course.pk] * 3 + [
        completed.course_id
    ]


def test_empty_map_and_invalid_role_are_empty() -> None:
    """Keep empty and ineligible accounts free of station data."""
    assert station_map_for(UserFactory(approved_trainee=True)) == ()
    assert station_map_for(UserFactory(approved_trainer=True)) == ()
    assert station_map_for(UserFactory(pending_trainee=True)) == ()
    assert station_map_for(UserFactory(rejected_user=True)) == ()


@pytest.mark.parametrize(
    "scale", [(1, 2, 1), (8, 7, 3)], ids=["small-1x2x1", "large-8x7x3"]
)
def test_station_map_query_count_is_constant(
    scale: tuple, django_assert_num_queries: object
) -> None:
    """Hold query count at four as courses, modules and skills increase."""
    course_count, module_count, skill_count = scale
    trainee = UserFactory(approved_trainee=True)
    for _ in range(course_count):
        enrollment = EnrollmentFactory(trainee=trainee)
        for order in range(1, module_count + 1):
            module = ModuleFactory(course=enrollment.course, order=order)
            module.skills.set(SkillFactory.create_batch(skill_count))
    with django_assert_num_queries(4):
        lines = station_map_for(trainee)
    assert sum(len(line.stations) for line in lines) == course_count * module_count
