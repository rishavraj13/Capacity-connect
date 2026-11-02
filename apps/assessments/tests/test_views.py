"""Exercise grouped authoring and safe trainee take/result HTTP workflows."""

from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments import services
from apps.assessments.constants import AttemptStatus
from apps.assessments.models import Attempt, AttemptAnswer, Questionnaire
from apps.assessments.tests.factories import (
    MOMENT,
    AttemptFactory,
    QuestionnaireFactory,
    ready_quiz,
)

pytestmark = pytest.mark.django_db


def quiz_post() -> dict:
    """Use timezone-aware deterministic dates on actual model forms."""
    return {
        "title": "HTTP quiz",
        "opens_at": (MOMENT - timedelta(hours=1)).isoformat(),
        "deadline": (MOMENT + timedelta(hours=1)).isoformat(),
        "duration_minutes": 5,
        "pass_percent": 50,
        "max_attempts": 2,
    }


def test_authoring_forms_derive_ownership_and_create_choices(client: Client) -> None:
    """Keep quiz/choice authoring reachable without accepting forged owner fields."""
    course = QuestionnaireFactory().course
    client.force_login(course.trainer)
    data = dict(
        quiz_post(), trainer=UserFactory(approved_trainer=True).pk, subject=99999
    )
    assert (
        client.post(reverse("assessments:create", args=[course.pk]), data).status_code
        == 302
    )
    quiz = Questionnaire.objects.get(title="HTTP quiz")
    assert quiz.trainer_id == course.trainer_id and quiz.subject_id == course.subject_id
    assert_grouped_question_created(client, quiz)


def test_question_edit_and_questionnaire_schedule_form(client: Client) -> None:
    """Persist grouped question changes and ordinary scheduling edits."""
    quiz, question, _ = ready_quiz()
    client.force_login(quiz.trainer)
    url = reverse("assessments:question_edit", args=[question.pk])
    assert client.get(url).context["form"].initial["correct_option"] == 1
    assert (
        client.post(
            url,
            {"text": "Edited", "options": "X\nY\nZ", "correct_option": 3, "marks": 4},
        ).status_code
        == 302
    )
    question.refresh_from_db()
    assert (
        question.text == "Edited" and question.options.get(is_correct=True).text == "Z"
    )
    data = dict(quiz_post(), title="Updated quiz")
    assert (
        client.post(reverse("assessments:edit", args=[quiz.pk]), data).status_code
        == 302
    )
    quiz.refresh_from_db()
    assert quiz.title == "Updated quiz"


def test_http_double_submit_changes_nothing(client: Client) -> None:
    """Make two take-page POSTs return one durable grade and answer set."""
    quiz, question, trainee = ready_quiz()
    client.force_login(trainee)
    assert client.post(reverse("assessments:start", args=[quiz.pk])).status_code == 302
    attempt = Attempt.objects.get(trainee=trainee)
    url = reverse("assessments:take", args=[attempt.pk])
    response = client.post(
        url, {f"question_{question.pk}": question.options.first().pk}
    )
    assert response.status_code == 302
    snapshot = Attempt.objects.values().get(pk=attempt.pk)
    assert client.post(url, {"question_999999": 999999}).status_code == 302
    assert (
        Attempt.objects.values().get(pk=attempt.pk) == snapshot
        and AttemptAnswer.objects.count() == 1
    )


def test_expired_take_get_finalizes_then_redirects_to_result(client: Client) -> None:
    """Apply the user-requested lazy-expiry exception to ordinary GET rendering."""
    quiz, _, trainee = ready_quiz()
    attempt = AttemptFactory(
        questionnaire=quiz, trainee=trainee, started_at=MOMENT - timedelta(hours=1)
    )
    client.force_login(trainee)
    response = client.get(reverse("assessments:take", args=[attempt.pk]))
    assert response.status_code == 302 and response.url == reverse(
        "assessments:result", args=[attempt.pk]
    )
    attempt.refresh_from_db()
    assert attempt.status == AttemptStatus.TIMED_OUT and attempt.submitted_at == MOMENT


def test_tampered_radio_fields_reject_whole_http_submission(client: Client) -> None:
    """Reject foreign question keys and invalid option choices before grading."""
    quiz, question, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    client.force_login(trainee)
    url = reverse("assessments:take", args=[attempt.pk])
    for data in ({"question_999999": 1}, {f"question_{question.pk}": 999999}):
        response = client.post(url, data)
        assert response.status_code == 200 and response.context["form"].errors
    assert not attempt.answers.exists()


def test_client_correctness_and_score_flags_are_ignored(client: Client) -> None:
    """Ignore forged flags and compute correctness from the database option."""
    quiz, question, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    client.force_login(trainee)
    data = {
        f"question_{question.pk}": question.options.last().pk,
        "is_correct": True,
        "score": 999,
        "passed": True,
    }
    assert (
        client.post(reverse("assessments:take", args=[attempt.pk]), data).status_code
        == 302
    )
    attempt.refresh_from_db()
    assert (
        attempt.score == 0
        and not attempt.passed
        and not attempt.answers.get().is_correct
    )


def test_start_window_rejection_is_feedback_and_metadata_contains_no_questions(
    client: Client,
) -> None:
    """Keep a premature start recoverable and a detail page free of paper content."""
    quiz, question, trainee = ready_quiz(opens_at=MOMENT + timedelta(minutes=1))
    client.force_login(trainee)
    response = client.post(reverse("assessments:start", args=[quiz.pk]), follow=True)
    assert response.status_code == 200 and b"start window" in response.content
    assert question.text.encode() not in response.content
    assert not Attempt.objects.exists()


def test_valid_csrf_allows_take_submission() -> None:
    """Keep server-rendered radio submission functional with HttpOnly CSRF cookies."""
    quiz, _, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    client = Client(enforce_csrf_checks=True)
    client.force_login(trainee)
    url = reverse("assessments:take", args=[attempt.pk])
    assert client.get(url).status_code == 200
    assert (
        client.post(
            url, {"csrfmiddlewaretoken": client.cookies["csrftoken"].value}
        ).status_code
        == 302
    )


def assert_grouped_question_created(client: Client, quiz: Questionnaire) -> None:
    """Check choice correctness through the grouped authoring form and detail."""
    add_url = reverse("assessments:question_add", args=[quiz.pk])
    assert (
        client.post(
            add_url,
            {"text": "Which?", "options": "A\nB", "correct_option": 2, "marks": 3},
        ).status_code
        == 302
    )
    question = quiz.questions.get()
    assert list(question.options.values_list("text", "is_correct")) == [
        ("A", False),
        ("B", True),
    ]
    assert (
        client.get(reverse("assessments:manage_detail", args=[quiz.pk])).status_code
        == 200
    )
