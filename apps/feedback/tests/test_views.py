"""Keep human feedback editing CSRF-protected and owner scoped."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import EnrollmentFactory
from apps.feedback.models import Feedback
from apps.feedback.tests.factories import FeedbackFactory

pytestmark = pytest.mark.django_db


def test_feedback_form_creates_and_edits_one_owned_row(client: object) -> None:
    """Ignore forged author/target fields and retain one editable row."""
    enrollment = EnrollmentFactory()
    client.force_login(enrollment.trainee)
    url = reverse("feedback:course_submit", args=[enrollment.course_id])
    assert client.get(url).status_code == 200
    data = {
        "rating": 4,
        "comment": "  <script>test</script> ",
        "author": 999,
        "resource": 999,
    }
    assert client.post(url, data).status_code == 302
    assert client.post(url, {"rating": 5, "comment": "Updated"}).status_code == 302
    row = Feedback.objects.get()
    assert (
        row.author == enrollment.trainee
        and row.course == enrollment.course
        and row.comment == "Updated"
    )
    assert client.get(reverse("feedback:mine")).status_code == 200


def test_other_feedback_author_cannot_edit_or_delete(client: object) -> None:
    """Exclude guessed IDs and ineligible target IDs before writes."""
    row = FeedbackFactory()
    client.force_login(UserFactory(approved_trainee=True))
    assert client.post(reverse("feedback:delete", args=[row.pk])).status_code == 404
    assert (
        client.post(
            reverse("feedback:course_submit", args=[row.course_id]), {"rating": 1}
        ).status_code
        == 404
    )
    row.refresh_from_db()
    assert row.rating == 4


def test_csrf_required_for_submit_and_delete() -> None:
    """Require a real token on all feedback mutations including edits."""
    enrollment = EnrollmentFactory()
    row = FeedbackFactory(author=enrollment.trainee, course=enrollment.course)
    client = Client(enforce_csrf_checks=True)
    client.force_login(enrollment.trainee)
    for url in (
        reverse("feedback:course_submit", args=[row.course_id]),
        reverse("feedback:delete", args=[row.pk]),
    ):
        assert client.post(url, {"rating": 5}).status_code == 403
    url = reverse("feedback:course_submit", args=[row.course_id])
    client.get(url)
    assert (
        client.post(
            url,
            {
                "rating": 5,
                "comment": "Valid",
                "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            },
        ).status_code
        == 302
    )
