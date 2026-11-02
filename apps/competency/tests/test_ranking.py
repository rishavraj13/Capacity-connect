"""Pin every ranking sub-rule against hand-computed exact Decimal fixtures."""

from decimal import Decimal

import pytest

from apps.catalog.tests.factories import SubjectFactory
from apps.competency.selectors import rank_trainers_for
from apps.competency.tests.factories import CompetencyFactory
from apps.courses.tests.factories import CourseFactory
from apps.feedback.tests.factories import FeedbackFactory
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


def rated(subject: object, proficiency: int, years: int, ratings: tuple) -> object:
    """Create one published course with independent feedback rows for exact means."""
    row = CompetencyFactory(
        subject=subject, proficiency=proficiency, years_experience=years
    )
    course = CourseFactory(trainer=row.trainer, subject=subject, is_published=True)
    for rating in ratings:
        FeedbackFactory(course=course, rating=rating)
    return row


def test_ranking_formula_examples_and_experience_cap() -> None:
    """Check A=1.0000, B=.6600 and unrated C=.7000 with capped experience."""
    subject = SubjectFactory()
    a = rated(subject, 5, 10, (5,))
    b = rated(subject, 3, 5, (4, 5))
    c = rated(subject, 5, 60, ())
    result = rank_trainers_for(subject)
    assert [row.trainer_id for row in result] == [
        a.trainer_id,
        c.trainer_id,
        b.trainer_id,
    ]
    assert [row.score for row in result] == [
        Decimal("1.0000"),
        Decimal("0.7000"),
        Decimal("0.6600"),
    ]
    assert result[1].avg_rating is None and result[1].rating_count == 0
    assert result[2].avg_rating == Decimal("4.5")


def test_ratings_average_rows_across_targets_and_only_ranked_subject() -> None:
    """Reject average-of-averages and unrelated subject ratings."""
    subject = SubjectFactory()
    row = rated(subject, 5, 10, (4, 5))
    resource = ResourceFactory(trainer=row.trainer, subject=subject)
    FeedbackFactory(course=None, resource=resource, rating=1)
    FeedbackFactory(course__trainer=row.trainer, rating=5)
    result = rank_trainers_for(subject)[0]
    assert result.rating_count == 3 and result.avg_rating.quantize(
        Decimal("0.00000001")
    ) == Decimal("3.33333333")
    assert result.score == Decimal("0.9000") and result.courses_delivered == 1


def test_ranking_ties_use_published_course_count_then_trainer_id() -> None:
    """Count only published courses of this subject when breaking exact ties."""
    subject = SubjectFactory()
    first = rated(subject, 5, 10, ())
    second = rated(subject, 5, 10, ())
    CourseFactory(trainer=second.trainer, subject=subject, is_published=True)
    CourseFactory(trainer=first.trainer, subject=subject, is_published=False)
    third = rated(subject, 5, 10, ())
    result = rank_trainers_for(subject)
    assert [row.trainer_id for row in result] == [
        second.trainer_id,
        first.trainer_id,
        third.trainer_id,
    ]
    assert [row.rank for row in result] == [1, 2, 3]


def test_equal_display_scores_are_ordered_by_unrounded_score() -> None:
    """Order close unequal scores before the ID tie-break despite equal displays."""
    subject = SubjectFactory()
    lower = rated(subject, 5, 10, tuple([4] * 100 + [5]))
    higher = rated(subject, 5, 10, tuple([4] * 99 + [5]))
    result = rank_trainers_for(subject)
    assert result[0].score == result[1].score == Decimal("0.9406")
    assert [row.trainer_id for row in result] == [higher.trainer_id, lower.trainer_id]


@pytest.mark.parametrize(
    "changes", [{"is_active": False}, {"is_approved": False}, {"role": "TRAINEE"}]
)
def test_ineligible_trainers_with_leftover_competencies_are_excluded(
    changes: dict,
) -> None:
    """Recheck role/approval/activity in SQL rather than trusting retained rows."""
    row = CompetencyFactory()
    for name, value in changes.items():
        setattr(row.trainer, name, value)
    row.trainer.save()
    assert rank_trainers_for(row.subject) == ()


@pytest.mark.parametrize("size", [1, 12], ids=["small", "large"])
def test_ranking_constant_query_count(
    size: int, django_assert_num_queries: object
) -> None:
    """Fetch rating/delivery aggregates once regardless of the trainer count."""
    subject = SubjectFactory(is_active=False)
    for _ in range(size):
        rated(subject, 5, 10, (4, 5))
    with django_assert_num_queries(1):
        result = rank_trainers_for(subject)
    assert len(result) == size
