"""Keep other trainees' participation and other trainers' drafts private."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.courses.models import ModuleProgress
from apps.courses.tests.factories import CourseFactory, EnrollmentFactory, ModuleFactory

pytestmark = pytest.mark.django_db


def test_other_trainee_enrollment_and_progress_are_404(client: Client) -> None:
    """Reject guessed ownership IDs before a progress service can run."""
    enrollment = EnrollmentFactory()
    module = ModuleFactory(course=enrollment.course)
    other = UserFactory(approved_trainee=True)
    client.force_login(other)
    assert client.post(reverse("courses:drop", args=[enrollment.pk])).status_code == 404
    assert (
        client.post(
            reverse("courses:complete_module", args=[enrollment.pk, module.pk])
        ).status_code
        == 404
    )
    mine = client.get(reverse("courses:my_courses"))
    assert list(mine.context["enrollments"]) == []
    assert not ModuleProgress.objects.exists()


def test_wrong_course_and_dropped_completion_are_blocked(client: Client) -> None:
    """Deny both cross-course module IDs and inactive participation writes."""
    enrollment = EnrollmentFactory()
    wrong = ModuleFactory()
    client.force_login(enrollment.trainee)
    assert (
        client.post(
            reverse("courses:complete_module", args=[enrollment.pk, wrong.pk])
        ).status_code
        == 404
    )
    module = ModuleFactory(course=enrollment.course)
    assert client.post(reverse("courses:drop", args=[enrollment.pk])).status_code == 302
    response = client.post(
        reverse("courses:complete_module", args=[enrollment.pk, module.pk]), follow=True
    )
    assert response.status_code == 200
    assert not ModuleProgress.objects.exists()


@pytest.mark.parametrize("actor", ["trainee", "trainer"])
def test_unpublished_course_is_hidden_from_unenrolled_others(
    client: Client, actor: str
) -> None:
    """Return 404 instead of exposing another trainer's private course metadata."""
    course = CourseFactory()
    client.force_login(UserFactory(**{f"approved_{actor}": True}))
    assert client.get(reverse("courses:detail", args=[course.pk])).status_code == 404
