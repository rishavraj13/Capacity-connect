"""Verify assessment presentation against the server-owned state and disclosure."""

import re
from datetime import timedelta

import pytest
from django.urls import reverse

from apps.assessments import services
from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.models import Option
from apps.assessments.tests.factories import AttemptFactory, QuestionFactory, ready_quiz
from apps.core import clock
from apps.core.tests.test_trainee_learning import learning_html
from apps.courses.models import Enrollment

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        ("open", "Start attempt"),
        ("upcoming", "Upcoming. Questionnaire is outside its start window."),
        ("closed", "Closed. Questionnaire is outside its start window."),
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


@pytest.mark.parametrize(
    "state",
    (
        "before_open",
        "at_open",
        "before_close",
        "at_close",
        "exhausted",
        "resumable",
        "expired",
        "unready",
        "dropped",
        "unpublished",
    ),
)
def test_assessment_start_matches_service_at_fixed_instant(
    client: object, state: str
) -> None:
    """Compare page and service on the same rows before the write changes them."""
    instant = clock.now()
    quiz, trainee = _start_fixture(instant, state)
    client.force_login(trainee)
    with clock.at(instant):
        response = client.get(reverse("assessments:detail", args=[quiz.pk]))
        html = response.content.decode()
        try:
            services.start_attempt(trainee, quiz)
        except AssessmentRuleError as error:
            assert "Start attempt" not in html and "Resume attempt" not in html
            if state == "dropped":
                assert response.status_code == 404
            else:
                assert error.message in html
        else:
            assert response.status_code == 200
            assert (
                "Resume attempt" if state == "resumable" else "Start attempt"
            ) in html


def _start_fixture(instant: object, state: str) -> tuple:
    """Set up time edges and persisted attempt states independently of the page."""
    tick = timedelta(microseconds=1)
    hour = timedelta(hours=1)
    opens_at = {"before_open": instant + tick, "at_open": instant}.get(
        state, instant - hour
    )
    deadline = {"before_close": instant + tick, "at_close": instant}.get(
        state, instant + hour
    )
    quiz, question, trainee = ready_quiz(
        opens_at=opens_at,
        deadline=deadline,
        max_attempts=1 if state == "exhausted" else 2,
    )
    _seed_start_attempt(quiz, trainee, state, instant)
    if state == "unready":
        question.options.all().delete()
    if state == "dropped":
        Enrollment.objects.filter(course=quiz.course, trainee=trainee).update(
            status="DROPPED"
        )
    if state == "unpublished":
        quiz.course.is_published = False
        quiz.course.save(update_fields=["is_published"])
    return quiz, trainee


def _seed_start_attempt(
    quiz: object, trainee: object, state: str, instant: object
) -> None:
    """Create only the attempt state needed by the parity fixture."""
    hour = timedelta(hours=1)
    if state in ("resumable", "expired", "exhausted"):
        AttemptFactory(
            questionnaire=quiz,
            trainee=trainee,
            started_at=instant - hour if state == "expired" else instant,
            status="TIMED_OUT" if state == "exhausted" else "IN_PROGRESS",
        )


def test_quiz_paper_html_unchanged_when_correct_option_changes(client: object) -> None:
    """Detect markers, value changes and reordering by flipping correctness in place."""
    quiz, question, trainee = ready_quiz()
    attempt = AttemptFactory(questionnaire=quiz, trainee=trainee)
    client.force_login(trainee)
    url = reverse("assessments:take", args=[attempt.pk])
    with clock.at(attempt.started_at):
        first = client.get(url).content.decode()
        right = question.options.get(is_correct=True)
        wrong = question.options.get(is_correct=False)
        Option.objects.filter(pk=right.pk).update(is_correct=False)
        Option.objects.filter(pk=wrong.pk).update(is_correct=True)
        second = client.get(url).content.decode()

    token = r'(name="csrfmiddlewaretoken" value=")[^"]+'
    assert 'type="radio"' in first
    assert re.sub(token, r"\1MASK", first) == re.sub(token, r"\1MASK", second)
