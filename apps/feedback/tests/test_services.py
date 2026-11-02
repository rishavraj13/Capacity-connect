"""Verify feedback eligibility, upserts, validation and insert collision recovery."""

from unittest.mock import patch

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.core.exceptions import CapacityConnectError
from apps.courses.tests.factories import EnrollmentFactory
from apps.feedback import services
from apps.feedback.models import Feedback
from apps.feedback.tests.factories import FeedbackFactory
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("status", ["ACTIVE", "DROPPED", "COMPLETED"])
def test_course_feedback_upsert_for_every_enrollment_status(status: str) -> None:
    """Keep a trainee's edit in the same row across participation history."""
    enrollment = EnrollmentFactory(status=status)
    first = services.submit_course_feedback(
        enrollment.trainee, enrollment.course, 4, "  Good  "
    )
    second = services.submit_course_feedback(
        enrollment.trainee, enrollment.course, 5, " Best "
    )
    assert first.pk == second.pk and Feedback.objects.count() == 1
    assert second.rating == 5 and second.comment == "Best"
    services.delete_feedback(enrollment.trainee, second)
    assert not Feedback.objects.exists()


@pytest.mark.parametrize(
    "trait", ["approved_trainer", "active_admin", "pending_trainee", "rejected_user"]
)
def test_only_approved_active_trainee_can_submit(trait: str) -> None:
    """Enforce roles independently of HTTP decorators."""
    row = EnrollmentFactory()
    with pytest.raises(CapacityConnectError):
        services.submit_course_feedback(UserFactory(**{trait: True}), row.course, 4, "")


def test_non_enrolled_course_and_unpublished_resource_are_refused() -> None:
    """Keep publication from granting course-feedback enrollment rights."""
    row = EnrollmentFactory()
    outsider = UserFactory(approved_trainee=True)
    with pytest.raises(CapacityConnectError):
        services.submit_course_feedback(outsider, row.course, 4, "")
    resource = ResourceFactory(is_published=False)
    with pytest.raises(CapacityConnectError):
        services.submit_resource_feedback(outsider, resource, 4, "")
    resource.is_published = True
    resource.save()
    assert (
        services.submit_resource_feedback(outsider, resource, 5, "").resource
        == resource
    )


@pytest.mark.parametrize("rating,comment", [(0, ""), (6, ""), (4, "x" * 2001)])
def test_invalid_feedback_returns_domain_error(rating: int, comment: str) -> None:
    """Keep invalid direct-service input out of persistence."""
    row = EnrollmentFactory()
    with pytest.raises(CapacityConnectError):
        services.submit_course_feedback(row.trainee, row.course, rating, comment)
    assert not Feedback.objects.exists()


def test_insert_race_recovers_and_updates_real_unique_winner() -> None:
    """Hit database uniqueness after a stale read then apply the new opinion."""
    enrollment = EnrollmentFactory()
    winner = FeedbackFactory(author=enrollment.trainee, course=enrollment.course)
    with patch("apps.feedback.services._existing", side_effect=[None, winner]):
        row = services.submit_course_feedback(
            enrollment.trainee, enrollment.course, 5, "Latest"
        )
    assert (
        row.pk == winner.pk
        and row.comment == "Latest"
        and Feedback.objects.count() == 1
    )


def test_other_author_cannot_delete_feedback() -> None:
    """Check ownership at the service boundary as well as in URL scopes."""
    with pytest.raises(CapacityConnectError, match="author"):
        services.delete_feedback(UserFactory(approved_trainee=True), FeedbackFactory())
