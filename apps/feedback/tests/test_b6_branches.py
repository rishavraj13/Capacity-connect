"""Prove unrecoverable conflicts and changing ownership remain clean failures."""

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core.exceptions import CapacityConnectError
from apps.courses.models import Course
from apps.courses.tests.factories import EnrollmentFactory
from apps.feedback import selectors, services
from apps.feedback.tests.factories import FeedbackFactory

pytestmark = pytest.mark.django_db


def test_feedback_collision_without_recoverable_winner_is_domain_error() -> None:
    """Hit a real unique collision while the stale read cannot recover its winner."""
    enrollment = EnrollmentFactory()
    FeedbackFactory(author=enrollment.trainee, course=enrollment.course)
    with patch("apps.feedback.services._existing", return_value=None):
        with pytest.raises(CapacityConnectError, match="conflict"):
            services.submit_course_feedback(
                enrollment.trainee, enrollment.course, 5, ""
            )


def test_summary_ownership_changed_after_lookup_returns_404(client: object) -> None:
    """Recheck actual ownership if reassignment happens between the two scopes."""
    row = FeedbackFactory()
    client.force_login(row.course.trainer)
    other = UserFactory(approved_trainer=True)
    original = selectors.managed_targets
    calls = 0

    def reassign(user: object, course: bool) -> object:
        """Move ownership immediately before the selector's second real read."""
        nonlocal calls
        calls += 1
        if calls == 2:
            Course.objects.filter(pk=row.course_id).update(trainer=other)
        return original(user, course)

    with patch("apps.feedback.selectors.managed_targets", side_effect=reassign):
        assert (
            client.get(
                reverse("feedback:course_summary", args=[row.course_id])
            ).status_code
            == 404
        )
