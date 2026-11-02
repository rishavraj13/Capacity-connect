"""Prove the take paper has no correctness data and result disclosure is bounded."""

from dataclasses import asdict

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments import selectors, services
from apps.assessments.constants import AttemptStatus
from apps.assessments.tests.factories import AttemptFactory, ready_quiz

pytestmark = pytest.mark.django_db


def test_paper_dataclasses_and_queries_have_no_correctness() -> None:
    """Make hidden correctness structurally absent rather than relying on templates."""
    quiz, _, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    with CaptureQueriesContext(connection) as queries:
        paper = selectors.paper_for(attempt)
    assert paper and all("is_correct" not in query["sql"] for query in queries)
    assert "is_correct" not in str(asdict(paper[0]))
    assert all(
        not hasattr(option, "is_correct")
        for question in paper
        for option in question.options
    )
    services.submit_attempt(trainee, attempt, {})
    assert selectors.paper_for(attempt) == ()


def test_take_html_contains_no_correct_option_markers(client: Client) -> None:
    """Render the real radio form without correctness keys or hidden markers."""
    quiz, question, trainee = ready_quiz()
    attempt = services.start_attempt(trainee, quiz)
    client.force_login(trainee)
    response = client.get(reverse("assessments:take", args=[attempt.pk]))
    assert response.status_code == 200
    for marker in (b"is_correct", b"correct_option", b"data-correct", b"(correct)"):
        assert marker not in response.content
    assert f'value="{question.options.first().pk}"'.encode() in response.content
    assert response.context["seconds_left"] > 0


def test_result_hides_correct_choice_until_quota_exhausted(client: Client) -> None:
    """Defer correct-choice text while further attempts remain."""
    quiz, question, trainee = ready_quiz(max_attempts=2)
    first = services.start_attempt(trainee, quiz)
    services.submit_attempt(trainee, first, {question.pk: question.options.last().pk})
    result = selectors.attempt_result(trainee, first.pk)
    assert (
        result.questions[0].correct_option is None
        and not result.questions[0].is_correct
    )
    client.force_login(trainee)
    url = reverse("assessments:result", args=[first.pk])
    assert b"Correct option:" not in client.get(url).content
    second = services.start_attempt(trainee, quiz)
    services.submit_attempt(trainee, second, {})
    assert b"Correct option:" in client.get(url).content
    assert (
        selectors.attempt_result(trainee, first.pk).questions[0].correct_option
        == question.options.first().text
    )


def test_staff_see_correct_choices_and_other_trainees_do_not() -> None:
    """Apply result scope before building any answer-bearing result data."""
    quiz, question, trainee = ready_quiz(max_attempts=2)
    attempt = AttemptFactory(
        questionnaire=quiz, trainee=trainee, status=AttemptStatus.SUBMITTED
    )
    for user in (quiz.course.trainer, UserFactory(active_admin=True)):
        assert (
            selectors.attempt_result(user, attempt.pk).questions[0].correct_option
            == question.options.first().text
        )
    for user in (
        UserFactory(approved_trainer=True),
        UserFactory(approved_trainee=True),
        UserFactory(pending_trainee=True),
    ):
        assert selectors.attempt_result(user, attempt.pk) is None
