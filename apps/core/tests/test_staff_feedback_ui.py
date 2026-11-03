"""Verify role-filtered feedback and dashboard statistics presentation."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.test_trainee_learning import learning_html
from apps.courses.tests.factories import CourseFactory
from apps.feedback.tests.factories import FeedbackFactory
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("kind", ("course", "resource"))
@pytest.mark.parametrize("admin", (False, True))
def test_feedback_summary_keeps_author_scope_and_escapes_comments(
    client: object, kind: str, admin: bool
) -> None:
    """Show five labelled meters and keep names in the Admin disclosure only."""
    target = CourseFactory() if kind == "course" else ResourceFactory()
    actor = UserFactory(active_admin=True) if admin else target.trainer
    client.force_login(actor)
    route = f"feedback:{kind}_summary"
    assert "No feedback yet." in learning_html(client, route, (target.pk,))
    author = UserFactory(
        approved_trainee=True, first_name="PrivateAuthor", last_name="Name"
    )
    relation = (
        {"course": target} if kind == "course" else {"course": None, "resource": target}
    )
    FeedbackFactory(
        author=author, rating=5, comment="<script>alert(1)</script>", **relation
    )
    FeedbackFactory(rating=3, **relation)
    html = learning_html(client, route, (target.pk,))
    assert html.count("<meter") == 5 and "5 stars: 1 response" in html
    assert ("PrivateAuthor Name" in html) == admin
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html and "<script>" not in html
    client.force_login(UserFactory(approved_trainer=True))
    assert client.get(reverse(route, args=[target.pk])).status_code == 404


def test_trainer_dashboard_empty_and_rated_course(client: object) -> None:
    """Render owner-only aggregates and the rating meter without fabricated data."""
    trainer = UserFactory(approved_trainer=True)
    client.force_login(trainer)
    assert "No own courses." in learning_html(client, "dashboards:trainer")
    course = CourseFactory(trainer=trainer, is_published=True)
    FeedbackFactory(course=course, rating=4)
    html = learning_html(client, "dashboards:trainer")
    assert "<caption>Trainer course statistics</caption>" in html
    assert ">Published<" in html and 'value="4.00"' in html
    assert reverse("assessments:course_list", args=[course.pk]) in html
    client.force_login(UserFactory(active_admin=True))
    assert client.get(reverse("dashboards:trainer")).status_code == 403
