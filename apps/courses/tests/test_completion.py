"""Exercise every authorized completion scenario through the single entry point."""

from unittest.mock import patch

import pytest

from apps.assessments import services as assessments
from apps.assessments.tests.factories import (
    MOMENT,
    QuestionFactory,
    QuestionnaireFactory,
)
from apps.certificates.models import Certificate
from apps.core import clock
from apps.courses import services
from apps.courses.completion import evaluate_completion
from apps.courses.completion_selectors import completion_status
from apps.courses.tests.completion_factories import completion_flow, pass_quiz
from apps.courses.tests.factories import (
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch: object) -> None:
    """Keep assessment windows and certificate dates independent of wall time."""
    monkeypatch.setattr(clock, "now", lambda: MOMENT)
    monkeypatch.setattr(clock, "today", lambda: MOMENT.date())


def test_modules_done_without_ready_quizzes_complete_without_certificate() -> None:
    """Allow module-only completion without inventing a certificate score."""
    enrollment = EnrollmentFactory()
    module = ModuleFactory(course=enrollment.course)
    QuestionnaireFactory(course=enrollment.course)
    services.complete_module(enrollment.trainee, enrollment, module)
    enrollment.refresh_from_db()
    assert enrollment.status == "COMPLETED" and not Certificate.objects.exists()


def test_last_passing_submit_completes_and_issues_once() -> None:
    """Trigger completion at the quiz when all stations were already done."""
    enrollment, module, quiz, question = completion_flow()
    services.complete_module(enrollment.trainee, enrollment, module)
    enrollment.refresh_from_db()
    assert enrollment.status == "ACTIVE"
    result = pass_quiz(enrollment, quiz, question)
    enrollment.refresh_from_db()
    assert enrollment.status == "COMPLETED" and result.passed
    assert Certificate.objects.filter(enrollment=enrollment).count() == 1
    assert not evaluate_completion(enrollment)
    assert Certificate.objects.count() == 1


def test_last_module_after_passing_quiz_completes_and_issues() -> None:
    """Trigger the same transition when the final station is completed later."""
    enrollment, module, quiz, question = completion_flow()
    pass_quiz(enrollment, quiz, question)
    assert not Certificate.objects.exists()
    services.complete_module(enrollment.trainee, enrollment, module)
    enrollment.refresh_from_db()
    assert enrollment.status == "COMPLETED" and Certificate.objects.count() == 1


def test_zero_modules_never_completes() -> None:
    """Avoid treating an empty course as a finished training program."""
    enrollment = EnrollmentFactory()
    assert not evaluate_completion(enrollment) and not Certificate.objects.exists()


def test_exhausted_failed_quizzes_keep_enrollment_active() -> None:
    """Require a passing submitted outcome even when all quota was used."""
    enrollment, module, quiz, question = completion_flow()
    services.complete_module(enrollment.trainee, enrollment, module)
    for _ in range(2):
        attempt = assessments.start_attempt(enrollment.trainee, quiz)
        assessments.submit_attempt(enrollment.trainee, attempt, {})
    assert not evaluate_completion(enrollment)
    assert completion_status(enrollment).questionnaires[0].attempts_left == 0
    assert not Certificate.objects.exists()


def test_completed_status_never_reverts_after_new_content() -> None:
    """Keep the completion record and original certificate policy immutable."""
    enrollment = EnrollmentFactory()
    services.complete_module(
        enrollment.trainee, enrollment, ModuleFactory(course=enrollment.course)
    )
    ModuleFactory(course=enrollment.course, order=2)
    QuestionnaireFactory(course=enrollment.course)
    assert not evaluate_completion(enrollment)
    assert completion_status(enrollment).is_complete


def test_dropped_is_ignored_then_reactivation_completes_history() -> None:
    """Evaluate retained complete history only once it becomes ACTIVE again."""
    enrollment = EnrollmentFactory(status="DROPPED")
    module = ModuleFactory(course=enrollment.course)
    ModuleProgressFactory(enrollment=enrollment, module=module)
    assert not evaluate_completion(enrollment)
    services.enroll(enrollment.trainee, enrollment.course)
    enrollment.refresh_from_db()
    assert enrollment.status == "COMPLETED"


def test_pdf_failure_preserves_passing_quiz_and_progress(
    caplog: object, settings: object
) -> None:
    """Rollback the completion savepoint without losing the triggering quiz grade."""
    enrollment, module, quiz, question = completion_flow()
    services.complete_module(enrollment.trainee, enrollment, module)
    with patch(
        "apps.certificates.services.render_certificate_pdf",
        side_effect=ValueError("bad PDF"),
    ):
        result = pass_quiz(enrollment, quiz, question)
    enrollment.refresh_from_db()
    assert (
        result.passed and result.answers.count() == 1 and enrollment.status == "ACTIVE"
    )
    assert enrollment.progress.count() == 1 and not Certificate.objects.exists()
    assert "Certificate generation failed" in caplog.text
    from pathlib import Path

    assert not list(Path(settings.PRIVATE_MEDIA_ROOT).rglob("*.pdf"))


def test_pdf_failure_preserves_last_module_progress() -> None:
    """Keep the final progress row when PDF creation fails from the module trigger."""
    enrollment, module, quiz, question = completion_flow()
    pass_quiz(enrollment, quiz, question)
    with patch(
        "apps.certificates.services.render_certificate_pdf",
        side_effect=ValueError("bad PDF"),
    ):
        services.complete_module(enrollment.trainee, enrollment, module)
    enrollment.refresh_from_db()
    assert enrollment.status == "ACTIVE" and enrollment.progress.count() == 1
    assert not Certificate.objects.exists()


@pytest.mark.parametrize("size", [1, 12], ids=["small", "large"])
def test_completion_status_constant_query_count(
    size: int, django_assert_num_queries: object
) -> None:
    """Hold completion data to two queries across ready quizzes and modules."""
    enrollment, module, quiz, question = completion_flow()
    for i in range(1, size):
        ModuleFactory(course=enrollment.course, order=i + 1)
        QuestionFactory(questionnaire__course=enrollment.course)
    with django_assert_num_queries(2):
        status = completion_status(enrollment)
    assert status.modules_total == size and len(status.questionnaires) == size


def test_modules_done_with_zero_questionnaires_complete_without_certificate() -> None:
    """Allow the explicitly authorized zero-ready-questionnaire case."""
    enrollment = EnrollmentFactory()
    ModuleProgressFactory(
        enrollment=enrollment, module=ModuleFactory(course=enrollment.course)
    )
    assert evaluate_completion(enrollment) and not Certificate.objects.exists()


def test_missed_quiz_deadline_keeps_enrollment_active(monkeypatch: object) -> None:
    """Leave an unmet expired quiz for an explicit later scheduling/quota decision."""
    from datetime import timedelta

    enrollment, module, _, _ = completion_flow()
    ModuleProgressFactory(enrollment=enrollment, module=module)
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(days=1))
    assert not evaluate_completion(enrollment)
    enrollment.refresh_from_db()
    assert enrollment.status == "ACTIVE"


def test_conditional_update_race_produces_one_transition_and_certificate() -> None:
    """Simulate a competing winner before the real conditional update sees zero rows."""
    from django.db.models.query import QuerySet

    from apps.certificates.services import issue_certificate

    enrollment, module, quiz, question = completion_flow()
    pass_quiz(enrollment, quiz, question)
    ModuleProgressFactory(enrollment=enrollment, module=module)
    original = QuerySet.update

    def competing(queryset: object, **values: object) -> int:
        """Persist the competing winner before repeating the same conditional write."""
        assert original(queryset, **values) == 1
        issue_certificate(enrollment)
        return original(queryset, **values)

    with patch.object(QuerySet, "update", competing):
        assert not evaluate_completion(enrollment)
    enrollment.refresh_from_db()
    assert enrollment.status == "COMPLETED" and Certificate.objects.count() == 1
