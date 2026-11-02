"""Deny guessed attempt/questionnaire identities at selector-filtered views."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments import services
from apps.assessments.models import AttemptAnswer
from apps.assessments.tests.factories import ready_quiz
from apps.core.exceptions import CapacityConnectError
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def test_trainee_cannot_read_or_submit_other_trainees_attempt(client: Client) -> None:
    """Keep another enrolled trainee's attempt and result hidden as 404."""
    quiz, question, owner = ready_quiz()
    attempt = services.start_attempt(owner, quiz)
    other = EnrollmentFactory(course=quiz.course).trainee
    client.force_login(other)
    url = reverse("assessments:take", args=[attempt.pk])
    assert client.get(url).status_code == client.post(url, {}).status_code == 404
    assert (
        client.get(reverse("assessments:result", args=[attempt.pk])).status_code == 404
    )
    assert not list(client.get(reverse("assessments:history")).context["attempts"])
    with pytest.raises(CapacityConnectError, match="owner"):
        services.submit_attempt(
            other, attempt, {question.pk: question.options.first().pk}
        )
    assert not AttemptAnswer.objects.exists()


def test_other_trainer_questionnaire_question_and_participation_are_404(
    client: Client,
) -> None:
    """Filter another trainer's object IDs before any private choices are read."""
    quiz, question, _ = ready_quiz()
    client.force_login(UserFactory(approved_trainer=True))
    for name in ("manage_detail", "edit", "participation", "question_add"):
        assert (
            client.get(reverse(f"assessments:{name}", args=[quiz.pk])).status_code
            == 404
        )
    assert (
        client.get(reverse("assessments:question_edit", args=[question.pk])).status_code
        == 404
    )
    assert (
        client.post(
            reverse("assessments:question_delete", args=[question.pk])
        ).status_code
        == 404
    )
    assert client.post(reverse("assessments:delete", args=[quiz.pk])).status_code == 404


def test_non_enrolled_trainee_cannot_start_quiz(client: Client) -> None:
    """Hide quiz metadata and starts from users outside its enrolled course scope."""
    quiz, _, _ = ready_quiz()
    client.force_login(UserFactory(approved_trainee=True))
    assert client.get(reverse("assessments:detail", args=[quiz.pk])).status_code == 404
    assert client.post(reverse("assessments:start", args=[quiz.pk])).status_code == 404
