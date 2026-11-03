"""Verify assessment presentation against the server-owned state and disclosure."""

from datetime import timedelta

import pytest

from apps.assessments import services
from apps.assessments.tests.factories import AttemptFactory, QuestionFactory, ready_quiz
from apps.core import clock
from apps.core.tests.test_trainee_learning import learning_html
from apps.courses.models import Enrollment

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        ("open", "Start attempt"),
        ("upcoming", "The start window has not opened yet."),
        ("closed", "The start window has ended."),
        ("exhausted", "Maximum attempts reached."),
        ("unready", "Questionnaire is not ready."),
        ("completed", "An active enrollment is required."),
    ),
)
def test_assessment_ticket_explains_start_state(
    client: object, state: str, expected: str
) -> None:
    """Expose metadata and one appropriate action without any question content."""
    now = clock.now()
    quiz, question, trainee = ready_quiz(
        opens_at=now + timedelta(hours=1 if state == "upcoming" else -2),
        deadline=now + timedelta(hours=-1 if state == "closed" else 2),
        max_attempts=1,
    )
    if state == "exhausted":
        AttemptFactory(questionnaire=quiz, trainee=trainee, status="TIMED_OUT")
    if state == "unready":
        question.options.all().delete()
    if state == "completed":
        Enrollment.objects.filter(course=quiz.course, trainee=trainee).update(
            status="COMPLETED"
        )
    client.force_login(trainee)
    html = learning_html(client, "assessments:detail", (quiz.pk,))
    assert expected in html and "Pass mark" in html
    assert (">Start attempt<" in html) == (state == "open")
    assert question.text not in html
    assert "Next departures" in learning_html(client, "assessments:mine")


def test_paper_groups_have_marks_and_no_correctness_marker(client: object) -> None:
    """Render both choices with equivalent markup and no correctness metadata."""
    now = clock.now()
    quiz, question, trainee = ready_quiz(
        opens_at=now - timedelta(hours=1), deadline=now + timedelta(hours=1)
    )
    QuestionFactory(questionnaire=quiz, marks=2)
    attempt = services.start_attempt(trainee, quiz)
    client.force_login(trainee)
    html = learning_html(client, "assessments:take", (attempt.pk,))
    assert "Question 1 of 2, 1 mark" in html and "Question 2 of 2, 2 marks" in html
    assert "Time remaining at page load:" in html and "Submission deadline:" in html
    assert html.count('type="radio"') == 4
    assert question.text in html and "Choice Alpha" in html and "Choice Beta" in html
    assert not any(
        marker in html.lower()
        for marker in ("is_correct", "data-correct", "correct-option", "correct-answer")
    )


@pytest.mark.parametrize("outcome", ("passed", "failed", "timed_out"))
def test_result_text_and_disclosure(client: object, outcome: str) -> None:
    """Show a result stamp and leave hidden choices absent until quota is spent."""
    now = clock.now()
    quiz, question, trainee = ready_quiz(
        opens_at=now - timedelta(hours=1),
        deadline=now + timedelta(hours=1),
        max_attempts=1 if outcome == "passed" else 2,
    )
    attempt = services.start_attempt(trainee, quiz)
    if outcome == "timed_out":
        with clock.at(now + timedelta(hours=2)):
            services.expire_attempt(trainee, attempt)
    else:
        option = question.options.get(is_correct=outcome == "passed")
        services.submit_attempt(trainee, attempt, {question.pk: option.pk})
    client.force_login(trainee)
    html = learning_html(client, "assessments:result", (attempt.pk,))
    assert (">PASS<" in html) == (outcome == "passed")
    assert (">FAIL<" in html) == (outcome != "passed")
    assert ("Correct option: Choice Alpha" in html) == (outcome == "passed")
    assert ("late and discarded" in html) == (outcome == "timed_out")
    assert '<th scope="col">Status</th>' in learning_html(client, "assessments:history")
