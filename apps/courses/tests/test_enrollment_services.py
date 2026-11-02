"""Exercise unique enrollment races and sequential, owner-scoped progress."""

from unittest.mock import patch

import pytest

from apps.accounts.constants import UserRole
from apps.accounts.tests.factories import UserFactory
from apps.core.exceptions import CapacityConnectError
from apps.courses import services
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Enrollment, ModuleProgress
from apps.courses.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)

pytestmark = pytest.mark.django_db


def test_enroll_is_unique_and_reactivates_dropped_history() -> None:
    """Reuse the same row and progress rather than duplicate participation."""
    trainee = UserFactory(approved_trainee=True)
    course = CourseFactory(is_published=True)
    enrolled = services.enroll(trainee, course)
    assert services.enroll(trainee, course).pk == enrolled.pk
    progress = ModuleProgressFactory(enrollment=enrolled, module__course=course)
    services.drop(trainee, enrolled)
    resumed = services.enroll(trainee, course)
    assert resumed.pk == enrolled.pk and resumed.status == EnrollmentStatus.ACTIVE
    assert ModuleProgress.objects.filter(pk=progress.pk).exists()
    Enrollment.objects.filter(pk=enrolled.pk).update(status=EnrollmentStatus.COMPLETED)
    with pytest.raises(CapacityConnectError, match="Already completed"):
        services.enroll(trainee, course)


@pytest.mark.parametrize(
    "changes",
    [{"is_active": False}, {"is_approved": False}, {"role": UserRole.TRAINER}],
    ids=["inactive", "unapproved", "wrong-role"],
)
def test_enroll_requires_current_eligible_trainee(changes: dict) -> None:
    """Check database role/approval state rather than trusting a stale instance."""
    trainee = UserFactory(approved_trainee=True)
    type(trainee).objects.filter(pk=trainee.pk).update(**changes)
    with pytest.raises(CapacityConnectError):
        services.enroll(trainee, CourseFactory(is_published=True))


def test_enroll_requires_published_course_and_valid_trainer() -> None:
    """Keep unpublished or ineligible-owner courses out of new participation."""
    trainee = UserFactory(approved_trainee=True)
    course = CourseFactory()
    with pytest.raises(CapacityConnectError):
        services.enroll(trainee, course)
    course.is_published = True
    course.save()
    course.trainer.is_approved = False
    course.trainer.save()
    with pytest.raises(CapacityConnectError):
        services.enroll(trainee, course)


def test_enrollment_unique_race_returns_existing_row() -> None:
    """Hit the real database unique constraint after simulating a stale first read."""
    existing = EnrollmentFactory()
    with patch(
        "apps.courses.enrollment_services._existing", side_effect=[None, existing]
    ):
        result = services.enroll(existing.trainee, existing.course)
    assert result.pk == existing.pk
    assert Enrollment.objects.count() == 1


def test_enrollment_race_without_recoverable_row_is_domain_error() -> None:
    """Never expose an IntegrityError or leave the caller's transaction broken."""
    existing = EnrollmentFactory()
    with patch("apps.courses.enrollment_services._existing", return_value=None):
        with pytest.raises(CapacityConnectError, match="Enrollment conflict"):
            services.enroll(existing.trainee, existing.course)
    assert Enrollment.objects.count() == 1


def test_sequential_completion_is_idempotent_and_finishes_module_only_course() -> None:
    """Keep progress ordered and finish module-only courses under the B5 policy."""
    enrollment = EnrollmentFactory()
    first = ModuleFactory(course=enrollment.course, order=1)
    second = ModuleFactory(course=enrollment.course, order=2)
    with pytest.raises(CapacityConnectError, match="in order"):
        services.complete_module(enrollment.trainee, enrollment, second)
    progress = services.complete_module(enrollment.trainee, enrollment, first)
    repeated = services.complete_module(enrollment.trainee, enrollment, first)
    assert repeated.pk == progress.pk and repeated.completed_at == progress.completed_at
    services.complete_module(enrollment.trainee, enrollment, second)
    enrollment.refresh_from_db()
    assert enrollment.status == EnrollmentStatus.COMPLETED
    assert enrollment.progress.count() == 2


def test_wrong_course_dropped_and_other_owners_cannot_change_progress() -> None:
    """Enforce course identity, lifecycle and ownership even outside HTTP views."""
    enrollment = EnrollmentFactory()
    wrong = ModuleFactory()
    with pytest.raises(CapacityConnectError, match="another course"):
        services.complete_module(enrollment.trainee, enrollment, wrong)
    module = ModuleFactory(course=enrollment.course)
    outsider = UserFactory(approved_trainee=True)
    for action in (
        lambda: services.drop(outsider, enrollment),
        lambda: services.complete_module(outsider, enrollment, module),
    ):
        with pytest.raises(CapacityConnectError, match="owner"):
            action()
    services.drop(enrollment.trainee, enrollment)
    with pytest.raises(CapacityConnectError, match="active"):
        services.complete_module(enrollment.trainee, enrollment, module)
    with pytest.raises(CapacityConnectError, match="active"):
        services.drop(enrollment.trainee, enrollment)
