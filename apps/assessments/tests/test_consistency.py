"""Protect derived course references and recover submission conflicts safely."""

from unittest.mock import patch

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments import services
from apps.assessments.constants import AttemptStatus
from apps.assessments.models import Attempt
from apps.assessments.tests.factories import AnswerFactory, ready_quiz
from apps.catalog.tests.factories import SubjectFactory
from apps.core.exceptions import CapacityConnectError
from apps.courses.services import update_course

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("field", ["subject"])
def test_course_changes_preserve_assessment_references(field: str) -> None:
    """Reject reassignment that would leave existing quiz ownership inconsistent."""
    quiz, _, _ = ready_quiz()
    admin = UserFactory(active_admin=True)
    value = (
        UserFactory(approved_trainer=True) if field == "trainer" else SubjectFactory()
    )
    with pytest.raises(CapacityConnectError, match="assessments"):
        update_course(admin, quiz.course, {field: value})
    quiz.course.refresh_from_db()
    assert quiz.course.trainer_id == quiz.trainer_id
    assert quiz.course.subject_id == quiz.subject_id


def test_unresolved_submit_collision_is_domain_error_and_rolls_back() -> None:
    """Keep an unfinished conflicting row intact without a partial final grade."""
    quiz, question, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    answer = AnswerFactory(attempt=attempt, question=question)
    snapshot = Attempt.objects.values().get(pk=attempt.pk)
    with pytest.raises(CapacityConnectError, match="conflict"):
        services.submit_attempt(
            trainee, attempt, {question.pk: answer.selected_option_id}
        )
    assert Attempt.objects.values().get(pk=attempt.pk) == snapshot
    assert attempt.answers.count() == 1 and attempt.status == AttemptStatus.IN_PROGRESS


def test_submission_domain_conflict_is_form_feedback(client: object) -> None:
    """Turn a service conflict into a retryable form error instead of a 500."""
    from django.urls import reverse

    quiz, _, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    client.force_login(trainee)
    with patch(
        "apps.assessments.services.submit_attempt",
        side_effect=CapacityConnectError("Submission conflict; retry."),
    ):
        response = client.post(reverse("assessments:take", args=[attempt.pk]), {})
    assert response.status_code == 200 and response.context["form"].non_field_errors()
