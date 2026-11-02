"""Prove exact SQL aggregates and fixed query counts for both dashboard handoffs."""

from decimal import Decimal

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import AttemptFactory, QuestionnaireFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.courses.tests.factories import CourseFactory, EnrollmentFactory
from apps.dashboards.selectors import admin_dashboard, trainer_dashboard
from apps.dashboards.tests.factories import analytics_dataset

pytestmark = pytest.mark.django_db


def test_admin_dashboard_exact_fake_dataset_numbers() -> None:
    """Count best submitted pairs once and keep dropped-only attempts out of cohort."""
    analytics_dataset()
    result = admin_dashboard()
    assert_admin_counts(result)
    assert_admin_assessments(result)


def test_empty_dashboard_has_explicit_zeros_and_no_division_errors() -> None:
    """Return stable zero buckets without requiring fixture rows."""
    result = admin_dashboard()
    assert (
        result.courses_total
        == result.pending_approvals
        == result.enrollments_total
        == 0
    )
    assert (
        result.assessments.average_best_percent
        == result.assessments.pass_rate_percent
        == Decimal("0.00")
    )
    assert result.participation.participation_rate_percent == Decimal("0.00")
    assert result.line_load == () and all(
        value == 0 for value in result.users_by_role.values()
    )


def test_trainer_dashboard_only_own_courses_and_weighted_totals() -> None:
    """Avoid unrelated courses and average course feedback over rows, not averages."""
    data = analytics_dataset()
    result = trainer_dashboard(data["trainer"])
    by_title = {row.title: row for row in result.courses}
    assert set(by_title) == {"Published own", "Draft own"}
    first = by_title["Published own"]
    assert (first.enrolled, first.active, first.completed, first.certificates) == (
        2,
        1,
        1,
        1,
    )
    assert first.avg_rating == Decimal("4.50") and first.rating_count == 2
    assert (
        result.totals.avg_rating == Decimal("3.67") and result.totals.rating_count == 3
    )
    assert result.totals.courses_total == 2 and result.totals.questionnaires == 2
    assert {link.questionnaire_id for link in result.questionnaires} == {
        q.pk for q in data["quizzes"][:2]
    }


@pytest.mark.parametrize("size", [1, 10], ids=["small", "large"])
def test_dashboard_constant_query_counts(
    size: int, django_assert_num_queries: object
) -> None:
    """Hold Admin at nine and trainer at two despite growing source datasets."""
    trainer = UserFactory(approved_trainer=True)
    query_sources(trainer, size)
    with django_assert_num_queries(9):
        admin = admin_dashboard()
    with django_assert_num_queries(2):
        own = trainer_dashboard(trainer)
    assert admin.enrollments_total == len(own.courses) == size


def test_ineligible_trainer_dashboard_is_empty() -> None:
    """Avoid exposing course or quiz rows outside an eligible trainer identity."""
    user = UserFactory(active_admin=True)
    result = trainer_dashboard(user)
    assert (
        result.courses == result.questionnaires == ()
        and result.totals.avg_rating is None
    )


def assert_admin_counts(result: object) -> None:
    """Pin entity/status/line buckets independently of best-pair statistics."""
    assert result.users_by_role == {"TRAINEE": 4, "TRAINER": 2, "ADMIN": 1}
    assert (
        result.pending_approvals == 1
        and result.courses_total == 3
        and result.courses_published == 2
    )
    assert result.enrollments_total == 4 and result.enrollments_by_status == {
        "ACTIVE": 2,
        "COMPLETED": 1,
        "DROPPED": 1,
    }
    assert [
        (r.subject_name, r.enrollments, r.active_enrollments) for r in result.line_load
    ] == [("Data Skills", 4, 2), ("Zero Enrollments", 0, 0)]
    assert result.certificates_total == 1 and result.certificates_by_grade == {
        "A": 1,
        "B": 0,
        "C": 0,
        "D": 0,
    }


def assert_admin_assessments(result: object) -> None:
    """Pin retake and participation denominator behavior in the sample dataset."""
    assert (
        result.assessments.questionnaires_total == 3
        and result.assessments.submitted_attempts == 4
    )
    assert (
        result.assessments.average_best_percent
        == result.assessments.pass_rate_percent
        == Decimal("66.67")
    )
    assert (
        result.participation.enrolled_trainees
        == result.participation.attempted_trainees
        == 2
    )
    assert result.participation.participation_rate_percent == Decimal("100.00")


def query_sources(trainer: object, size: int) -> None:
    """Populate multiple subjects, courses, enrollments and retakes for query proofs."""
    for _ in range(size):
        course = CourseFactory(trainer=trainer, subject=SubjectFactory())
        trainee = EnrollmentFactory(course=course).trainee
        quiz = QuestionnaireFactory(course=course)
        AttemptFactory(
            questionnaire=quiz,
            trainee=trainee,
            status="SUBMITTED",
            percent=80,
            passed=True,
        )
        AttemptFactory(
            questionnaire=quiz,
            trainee=trainee,
            status="SUBMITTED",
            percent=60,
            passed=True,
        )


def test_best_pair_average_rounds_half_up_without_sqlite_sum_drift() -> None:
    """Keep a 0.005 mean at 0.01 when SQLite sums many cent-valued grades."""
    from apps.assessments.models import Attempt, Questionnaire
    from apps.assessments.tests.factories import MOMENT

    course = CourseFactory()
    trainee = UserFactory(approved_trainee=True)
    quizzes = Questionnaire.objects.bulk_create(
        QuestionnaireFactory.build_batch(1000, course=course)
    )
    Attempt.objects.bulk_create(
        [
            Attempt(
                questionnaire=q,
                trainee=trainee,
                started_at=MOMENT,
                status="SUBMITTED",
                percent=Decimal("0.01") if i < 500 else Decimal("0.00"),
            )
            for i, q in enumerate(quizzes)
        ]
    )
    assert admin_dashboard().assessments.average_best_percent == Decimal("0.01")
