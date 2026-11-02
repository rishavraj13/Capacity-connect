"""Verify persisted role eligibility, ownership and explicit course lifecycle writes."""

from datetime import date

import pytest

from apps.accounts.constants import UserRole
from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.core.exceptions import CapacityConnectError
from apps.courses import services
from apps.courses.tests.factories import (
    CourseFactory,
    ModuleFactory,
    ModuleProgressFactory,
)
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


def course_data(**changes: object) -> dict:
    """Keep required date input consistent across boundary tests."""
    return {
        "title": "Training",
        "description": "Details",
        "subject": SubjectFactory(),
        "start_date": date(2026, 1, 1),
        "end_date": date(2026, 2, 1),
        **changes,
    }


def test_create_update_and_publication_are_allowlisted() -> None:
    """Ignore forged owner/publish inputs while permitting Admin assignment."""
    owner = UserFactory(approved_trainer=True)
    other = UserFactory(approved_trainer=True)
    course = services.create_course(
        owner, course_data(trainer=other, is_published=True)
    )
    assert course.trainer == owner and not course.is_published
    updated = services.update_course(
        owner, course, {"title": "Updated", "is_published": True}
    )
    assert updated.title == "Updated" and not updated.is_published
    assert services.publish(owner, course).is_published
    assert not services.unpublish(owner, course).is_published
    admin = UserFactory(active_admin=True)
    assigned = services.create_course(admin, course_data(trainer=other))
    assert assigned.trainer == other
    assert services.update_course(admin, assigned, {"trainer": owner}).trainer == owner


@pytest.mark.parametrize(
    "changes",
    [{"is_active": False}, {"is_approved": False}, {"role": UserRole.TRAINEE}],
    ids=["inactive", "unapproved", "wrong-role"],
)
def test_invalid_trainer_accounts_are_rejected(changes: dict) -> None:
    """Reject current persisted role/approval/active failures despite stale objects."""
    actor = UserFactory(approved_trainer=True)
    type(actor).objects.filter(pk=actor.pk).update(**changes)
    with pytest.raises(CapacityConnectError):
        services.create_course(actor, course_data())
    admin = UserFactory(active_admin=True)
    with pytest.raises(CapacityConnectError):
        services.create_course(admin, course_data(trainer=actor))


def test_admin_requires_trainer_and_active_subject_assignments() -> None:
    """Keep missing/retired assignments as clean domain errors."""
    admin = UserFactory(active_admin=True)
    with pytest.raises(CapacityConnectError):
        services.create_course(admin, course_data())
    retired = SubjectFactory(is_active=False)
    owner = UserFactory(approved_trainer=True)
    with pytest.raises(CapacityConnectError):
        services.create_course(owner, course_data(subject=retired))
    course = CourseFactory(trainer=owner)
    with pytest.raises(CapacityConnectError):
        services.update_course(owner, course, {"subject": retired})
    course.subject.is_active = False
    course.subject.save()
    assert (
        services.update_course(owner, course, {"title": "History"}).title == "History"
    )


def test_ownership_dates_and_resource_associations() -> None:
    """Deny other trainers and preserve existing resource associations on edits."""
    course = CourseFactory()
    outsider = UserFactory(approved_trainer=True)
    for action in (services.publish, services.unpublish):
        with pytest.raises(CapacityConnectError):
            action(outsider, course)
    with pytest.raises(CapacityConnectError):
        services.update_course(outsider, course, {"title": "Stolen"})
    with pytest.raises(CapacityConnectError):
        services.update_course(course.trainer, course, {"end_date": date(2025, 1, 1)})
    ResourceFactory(course=course, trainer=course.trainer, subject=course.subject)
    with pytest.raises(CapacityConnectError):
        services.update_course(course.trainer, course, {"subject": SubjectFactory()})


def test_module_writes_validate_order_owner_and_progress() -> None:
    """Keep order conflicts recoverable and progressed modules undeletable."""
    course = CourseFactory()
    first = services.add_module(course.trainer, course, {"title": "One", "order": 1})
    with pytest.raises(CapacityConnectError):
        services.add_module(course.trainer, course, {"title": "Duplicate", "order": 1})
    second = services.add_module(course.trainer, course, {"title": "Two", "order": 2})
    with pytest.raises(CapacityConnectError):
        services.update_module(course.trainer, second, {"order": 1})
    updated = services.update_module(
        course.trainer, first, {"title": "Updated", "skills": []}
    )
    assert updated.title == "Updated"
    ModuleProgressFactory(module=first, enrollment__course=course)
    with pytest.raises(CapacityConnectError):
        services.delete_module(course.trainer, first)
    services.delete_module(course.trainer, second)


def test_other_trainers_cannot_write_modules() -> None:
    """Enforce ownership even when callers bypass selector-filtered views."""
    module = ModuleFactory()
    outsider = UserFactory(approved_trainer=True)
    with pytest.raises(CapacityConnectError):
        services.add_module(outsider, module.course, {"title": "Bad", "order": 2})
    with pytest.raises(CapacityConnectError):
        services.update_module(outsider, module, {"title": "Bad"})
    with pytest.raises(CapacityConnectError):
        services.delete_module(outsider, module)


def test_module_title_update_keeps_skills_when_not_submitted() -> None:
    """Treat missing M2M input as preservation rather than implicit removal."""
    from apps.catalog.tests.factories import SkillFactory

    module = ModuleFactory()
    skill = SkillFactory()
    module.skills.add(skill)
    updated = services.update_module(
        module.course.trainer, module, {"title": "Renamed"}
    )
    assert list(updated.skills.all()) == [skill]


def test_module_delete_progress_race_is_domain_error() -> None:
    """Catch database protection if progress appears after the initial guard."""
    from unittest.mock import patch

    progress = ModuleProgressFactory()
    with patch("django.db.models.query.QuerySet.exists", return_value=False):
        with pytest.raises(CapacityConnectError, match="progress"):
            services.delete_module(progress.enrollment.course.trainer, progress.module)
    assert type(progress).objects.filter(pk=progress.pk).exists()
