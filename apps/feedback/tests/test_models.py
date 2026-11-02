"""Exercise every database boundary independently of feedback services."""

import pytest
from django.db import IntegrityError, transaction

from apps.feedback.tests.factories import FeedbackFactory
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("rating", [0, 6])
def test_rating_database_bounds(rating: int) -> None:
    """Prevent invalid ratings even when form validation is bypassed."""
    with pytest.raises(IntegrityError), transaction.atomic():
        FeedbackFactory(rating=rating)


@pytest.mark.parametrize("target", ["none", "both"])
def test_exactly_one_target_constraint(target: str) -> None:
    """Disallow ambiguous or unassigned feedback records."""
    data = {"course": None} if target == "none" else {"resource": ResourceFactory()}
    with pytest.raises(IntegrityError), transaction.atomic():
        FeedbackFactory(**data)


@pytest.mark.parametrize("resource", [False, True])
def test_unique_author_per_target(resource: bool) -> None:
    """Keep course and resource opinions unique under direct concurrent writes."""
    row = FeedbackFactory(
        **({"course": None, "resource": ResourceFactory()} if resource else {})
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        FeedbackFactory(author=row.author, course=row.course, resource=row.resource)
