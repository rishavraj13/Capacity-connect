"""Verify course visibility and annotated counts without list-page N+1 reads."""

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.courses import selectors
from apps.courses.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)

pytestmark = pytest.mark.django_db


def test_visibility_includes_enrolled_unpublished_courses() -> None:
    """Retain access after unpublishing but hide another trainer's private work."""
    course = CourseFactory()
    trainee = UserFactory(approved_trainee=True)
    outsider = UserFactory(approved_trainer=True)
    admin = UserFactory(active_admin=True)
    assert course in selectors.visible_courses(course.trainer)
    assert course in selectors.visible_courses(admin)
    assert course not in selectors.visible_courses(outsider)
    assert course not in selectors.visible_courses(trainee)
    EnrollmentFactory(trainee=trainee, course=course)
    assert course in selectors.visible_courses(trainee)
    assert not selectors.managed_courses(trainee).exists()
    assert not selectors.visible_courses(UserFactory(pending_trainee=True)).exists()
    assert list(selectors.trainer_courses(course.trainer)) == [course]


def test_enrollment_and_participant_counts_have_one_query(
    django_assert_num_queries: object,
) -> None:
    """Annotate done/total counts without multiplying rows or lazy name queries."""
    enrollment = EnrollmentFactory()
    modules = ModuleFactory.create_batch(3, course=enrollment.course)
    ModuleProgressFactory(enrollment=enrollment, module=modules[0])
    with django_assert_num_queries(1):
        rows = list(selectors.enrollments_for(enrollment.trainee))
        assert [
            (row.modules_done, row.modules_total, row.course.title) for row in rows
        ] == [(1, 3, enrollment.course.title)]
    with django_assert_num_queries(1):
        participants = list(
            selectors.course_participants(enrollment.course.trainer, enrollment.course)
        )
        assert participants[0].modules_done == 1
        assert participants[0].trainee.username == enrollment.trainee.username
    assert not selectors.course_participants(
        UserFactory(approved_trainer=True), enrollment.course
    ).exists()
    assert not selectors.enrollments_for(UserFactory(approved_trainer=True)).exists()
