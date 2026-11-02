"""Freeze station ordering after progress without withdrawing enrolled access."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory
from apps.core.exceptions import CapacityConnectError
from apps.courses import services
from apps.courses.constants import StationState
from apps.courses.selectors import station_map_for
from apps.courses.tests.factories import (
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("position", [1, 2], ids=["progressed-module", "other-module"])
def test_any_progress_freezes_existing_module_order(position: int) -> None:
    """Preserve the sequence for every station once a course has any progress."""
    enrollment = EnrollmentFactory()
    modules = {i: ModuleFactory(course=enrollment.course, order=i) for i in (1, 2)}
    ModuleProgressFactory(enrollment=enrollment, module=modules[1])
    with pytest.raises(CapacityConnectError, match="order"):
        services.update_module(
            enrollment.course.trainer, modules[position], {"order": 5}
        )


def test_progress_allows_only_appended_modules() -> None:
    """Reject gaps while still permitting append-only course extension."""
    enrollment = EnrollmentFactory()
    first = ModuleFactory(course=enrollment.course, order=1)
    ModuleProgressFactory(enrollment=enrollment, module=first)
    with pytest.raises(CapacityConnectError, match="order"):
        services.add_module(
            enrollment.course.trainer, enrollment.course, {"title": "Gap", "order": 3}
        )
    added = services.add_module(
        enrollment.course.trainer, enrollment.course, {"title": "Append", "order": 2}
    )
    assert added.order == 2


def test_progress_still_allows_title_and_skill_edits() -> None:
    """Keep descriptive edits available without rewriting historical station order."""
    progress = ModuleProgressFactory()
    skill = SkillFactory()
    updated = services.update_module(
        progress.module.course.trainer,
        progress.module,
        {"title": "New title", "order": progress.module.order, "skills": [skill]},
    )
    assert updated.title == "New title" and list(updated.skills.all()) == [skill]


def test_unpublished_enrollment_keeps_access_and_module_progress(
    client: Client,
) -> None:
    """Withdraw new enrollment while retaining an enrolled trainee's learning path."""
    enrollment = EnrollmentFactory()
    module = ModuleFactory(course=enrollment.course)
    services.unpublish(enrollment.course.trainer, enrollment.course)
    client.force_login(enrollment.trainee)
    assert (
        client.get(reverse("courses:detail", args=[enrollment.course_id])).status_code
        == 200
    )
    services.complete_module(enrollment.trainee, enrollment, module)
    with pytest.raises(CapacityConnectError, match="published"):
        services.enroll(UserFactory(approved_trainee=True), enrollment.course)


def test_active_all_done_station_map_has_no_current() -> None:
    """Keep an all-done ACTIVE enrollment ready for future quiz completion rules."""
    enrollment = EnrollmentFactory()
    for order in (1, 2):
        module = ModuleFactory(course=enrollment.course, order=order)
        services.complete_module(enrollment.trainee, enrollment, module)
    states = [
        station.state
        for line in station_map_for(enrollment.trainee)
        for station in line.stations
    ]
    assert states == [StationState.DONE, StationState.DONE]
    assert StationState.CURRENT not in states


def test_admin_course_form_can_reassign_trainer(client: Client) -> None:
    """Prove the existing Admin form supports reassignment without adding features."""
    enrollment = EnrollmentFactory()
    course = enrollment.course
    new_trainer = UserFactory(approved_trainer=True)
    client.force_login(UserFactory(active_admin=True))
    response = client.post(
        reverse("courses:edit", args=[course.pk]),
        {
            "title": course.title,
            "subject": course.subject_id,
            "trainer": new_trainer.pk,
            "start_date": course.start_date.isoformat(),
            "end_date": course.end_date.isoformat(),
        },
    )
    assert response.status_code == 302
    course.refresh_from_db()
    assert course.trainer_id == new_trainer.pk
