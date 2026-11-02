"""Pin exact summary math, anonymity and dataset-independent query budgets."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory
from apps.feedback import selectors
from apps.feedback.tests.factories import FeedbackFactory

pytestmark = pytest.mark.django_db


def test_summary_math_and_all_rating_buckets() -> None:
    """Compute one-third averages with half-up Decimal rounding and stable zeros."""
    course = CourseFactory()
    empty = selectors.feedback_summary(course)
    assert empty.count == 0 and empty.average == Decimal("0.00")
    for rating in (1, 1, 2):
        FeedbackFactory(course=course, rating=rating)
    result = selectors.feedback_summary(course)
    assert result.average == Decimal("1.33") and result.distribution == {
        1: 2,
        2: 1,
        3: 0,
        4: 0,
        5: 0,
    }


def test_trainer_anonymity_admin_identity_and_escaped_comments(client: object) -> None:
    """Keep identifying author fields out of trainer DTOs and escape XSS."""
    row = FeedbackFactory(
        author__first_name="PrivateAuthor", comment="<script>alert(1)</script>"
    )
    url = reverse("feedback:course_summary", args=[row.course_id])
    client.force_login(row.course.trainer)
    response = client.get(url)
    assert (
        b"PrivateAuthor" not in response.content and b"<script>" not in response.content
    )
    assert b"&lt;script&gt;" in response.content
    assert response.context["page"][0].author_name is None
    client.force_login(UserFactory(active_admin=True))
    assert b"PrivateAuthor" in client.get(url).content
    assert (
        selectors.feedback_page(UserFactory(approved_trainer=True), row.course) is None
    )


@pytest.mark.parametrize("size", [1, 25], ids=["small", "large"])
def test_feedback_query_counts_and_pagination(
    size: int, django_assert_num_queries: object
) -> None:
    """Keep summary at one and paginated staff comments at three queries."""
    course = CourseFactory()
    FeedbackFactory.create_batch(size, course=course)
    with django_assert_num_queries(1):
        assert selectors.feedback_summary(course).count == size
    with django_assert_num_queries(3):
        page = selectors.feedback_page(course.trainer, course)
        assert len(page) == min(size, 20)


def test_own_feedback_list_is_scoped() -> None:
    """Return no retained opinions for an ineligible trainee identity."""
    row = FeedbackFactory()
    assert list(selectors.feedback_for_trainee(row.author)) == [row]
    assert not selectors.feedback_for_trainee(
        UserFactory(pending_trainee=True)
    ).exists()
