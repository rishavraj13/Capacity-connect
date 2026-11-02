"""Prove deadline/usage/participation contracts without dataset-size query growth."""

from datetime import timedelta
from decimal import Decimal

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments import selectors
from apps.assessments.constants import AttemptStatus, DepartureStatus
from apps.assessments.tests.factories import (
    MOMENT,
    AttemptFactory,
    QuestionnaireFactory,
    ready_quiz,
)
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def test_departures_filter_status_quota_passes_and_order() -> None:
    """Include only future available ACTIVE-enrollment quizzes in deadline order."""
    trainee = UserFactory(approved_trainee=True)
    quizzes = [
        QuestionnaireFactory(max_attempts=2, deadline=MOMENT + timedelta(minutes=i + 1))
        for i in range(6)
    ]
    for quiz in quizzes:
        EnrollmentFactory(trainee=trainee, course=quiz.course)
    exclude_unavailable(quizzes, trainee)
    departures = selectors.next_deadlines_for(trainee)
    assert [row.questionnaire_id for row in departures] == [
        quizzes[0].pk,
        quizzes[5].pk,
    ]
    assert [row.status for row in departures] == [
        DepartureStatus.UPCOMING,
        DepartureStatus.OPEN,
    ]
    assert len(selectors.next_deadlines_for(trainee, limit=1)) == 1


def test_questionnaire_usage_includes_completed_but_excludes_dropped() -> None:
    """Annotate total usage/remaining/resume metadata on retained enrolled quizzes."""
    quiz, _, trainee = ready_quiz(max_attempts=2)
    attempt = AttemptFactory(questionnaire=quiz, trainee=trainee)
    row = selectors.trainee_questionnaires(trainee).get(pk=quiz.pk)
    assert (row.attempts_used, row.attempts_left, row.open_attempt_id) == (
        1,
        1,
        attempt.pk,
    )
    quiz.course.enrollments.update(status="COMPLETED")
    assert selectors.trainee_questionnaires(trainee).filter(pk=quiz.pk).exists()
    assert selectors.next_deadlines_for(trainee) == ()
    quiz.course.enrollments.update(status="DROPPED")
    assert not selectors.trainee_questionnaires(trainee).exists()


def test_participation_includes_zero_and_uses_attempted_denominators() -> None:
    """Keep enrolled zero-attempt rows while averaging only attempted trainees."""
    quiz = QuestionnaireFactory(max_attempts=3)
    zero, success, timeout = [
        EnrollmentFactory(course=quiz.course).trainee for _ in range(3)
    ]
    participation_attempts(quiz, success, timeout)
    rows, stats = selectors.participation(quiz.course.trainer, quiz)
    by_user = {row.trainee_id: row for row in rows}
    assert (
        by_user[zero.pk].attempts_used == 0 and by_user[zero.pk].last_attempt_at is None
    )
    assert by_user[success.pk].attempts_used == 2 and by_user[
        success.pk
    ].best_percent == Decimal("80.00")
    assert (stats.enrolled, stats.attempted, stats.passed) == (3, 2, 1)
    assert stats.average_best_percent == Decimal(
        "40.00"
    ) and stats.pass_rate == Decimal("50.00")
    assert selectors.participation(UserFactory(approved_trainer=True), quiz) is None


def test_zero_participation_statistics_and_b5_handoff() -> None:
    """Return stable zeros and expose successful quiz IDs without marking completion."""
    quiz, _, trainee = ready_quiz()
    rows, stats = selectors.participation(quiz.trainer, quiz)
    assert len(rows) == 1 and stats.average_best_percent == stats.pass_rate == Decimal(
        "0.00"
    )
    assert not selectors.has_passed(trainee, quiz)
    AttemptFactory(
        questionnaire=quiz,
        trainee=trainee,
        passed=True,
        status=AttemptStatus.SUBMITTED,
        percent=100,
    )
    enrollment = quiz.course.enrollments.get(trainee=trainee)
    assert selectors.has_passed(trainee, quiz)
    assert selectors.passed_questionnaire_ids(enrollment) == {quiz.pk}


@pytest.mark.parametrize("size", [1, 12], ids=["small", "large"])
def test_deadline_and_questionnaire_query_counts(
    size: int, django_assert_num_queries: object
) -> None:
    """Hold departures and annotated quiz lists to one query each."""
    trainee = UserFactory(approved_trainee=True)
    for _ in range(size):
        quiz = QuestionnaireFactory(max_attempts=2)
        EnrollmentFactory(trainee=trainee, course=quiz.course)
        AttemptFactory(
            questionnaire=quiz, trainee=trainee, status=AttemptStatus.SUBMITTED
        )
    with django_assert_num_queries(1):
        assert len(selectors.next_deadlines_for(trainee)) == min(size, 5)
    with django_assert_num_queries(1):
        quizzes = list(selectors.trainee_questionnaires(trainee))
        assert all(quiz.course.title and quiz.subject.name for quiz in quizzes)
    assert len(quizzes) == size


@pytest.mark.parametrize("size", [1, 20], ids=["small", "large"])
def test_participation_query_count(
    size: int, django_assert_num_queries: object
) -> None:
    """Keep participation authorization and all aggregate rows at two queries."""
    quiz = QuestionnaireFactory(max_attempts=2)
    for _ in range(size):
        trainee = EnrollmentFactory(course=quiz.course).trainee
        AttemptFactory(
            questionnaire=quiz, trainee=trainee, status=AttemptStatus.SUBMITTED
        )
    with django_assert_num_queries(2):
        rows, stats = selectors.participation(quiz.trainer, quiz)
    assert len(rows) == stats.attempted == size


def test_ineligible_users_have_no_departures() -> None:
    """Keep annotated aliases safe even when the result is an empty scoped queryset."""
    assert selectors.next_deadlines_for(UserFactory(pending_trainee=True)) == ()


def exclude_unavailable(quizzes: list, trainee: object) -> None:
    """Exclude passed, exhausted, dropped and elapsed quizzes independently."""
    quizzes[0].opens_at = MOMENT + timedelta(seconds=1)
    quizzes[0].save()
    AttemptFactory(
        questionnaire=quizzes[1],
        trainee=trainee,
        passed=True,
        status=AttemptStatus.SUBMITTED,
    )
    quizzes[2].max_attempts = 1
    quizzes[2].save()
    AttemptFactory(
        questionnaire=quizzes[2], trainee=trainee, status=AttemptStatus.TIMED_OUT
    )
    quizzes[3].course.enrollments.update(status="DROPPED")
    quizzes[4].deadline = MOMENT
    quizzes[4].save()


def participation_attempts(quiz: object, success: object, timeout: object) -> None:
    """Create two grades for one trainee and a timeout for another."""
    AttemptFactory(
        questionnaire=quiz,
        trainee=success,
        status=AttemptStatus.SUBMITTED,
        percent=Decimal("40.00"),
    )
    AttemptFactory(
        questionnaire=quiz,
        trainee=success,
        status=AttemptStatus.SUBMITTED,
        percent=Decimal("80.00"),
        passed=True,
    )
    AttemptFactory(questionnaire=quiz, trainee=timeout, status=AttemptStatus.TIMED_OUT)
