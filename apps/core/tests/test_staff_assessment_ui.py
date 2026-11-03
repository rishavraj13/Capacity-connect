"""Exercise staff authoring and analytics HTML without altering ownership."""

from datetime import timedelta

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments.constants import (
    MAX_ATTEMPTS,
    MAX_DURATION_MINUTES,
    MAX_PASS_PERCENT,
)
from apps.assessments.tests.factories import (
    AnswerFactory,
    AttemptFactory,
    QuestionFactory,
    QuestionnaireFactory,
)
from apps.core import clock
from apps.core.tests.test_trainee_learning import learning_html
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(params=("owner", "admin"))
def staff_quiz(client: object, request: object) -> object:
    """Run each shared staff presentation assertion under both allowed roles."""
    quiz = QuestionnaireFactory()
    client.force_login(
        quiz.trainer if request.param == "owner" else UserFactory(active_admin=True)
    )
    return quiz


def _status_quiz(quiz: object, status: str) -> None:
    """Arrange consistent status fixtures under the same rendered clock."""
    now = clock.now()
    quiz.opens_at = now + timedelta(hours=1 if status == "Upcoming" else -2)
    quiz.deadline = now + timedelta(hours=-1 if status == "Closed" else 2)
    quiz.save(update_fields=["opens_at", "deadline"])
    if status != "Draft / not ready":
        QuestionFactory(questionnaire=quiz)


@pytest.mark.parametrize("status", ("Draft / not ready", "Upcoming", "Open", "Closed"))
def test_authoring_status_and_delete_confirmation(
    client: object, staff_quiz: object, status: str
) -> None:
    """Render shared state labels and explicit CSRF-protected delete controls."""
    quiz = staff_quiz
    _status_quiz(quiz, status)
    listing = learning_html(client, "assessments:course_list", (quiz.course_id,))
    detail = learning_html(client, "assessments:manage_detail", (quiz.pk,))
    assert all(f">{status}<" in html for html in (listing, detail))
    assert "Maximum attempts" in detail and "Pass mark" in listing
    delete = reverse("assessments:delete", args=[quiz.pk])
    assert f'<form method="post" action="{delete}">' in detail
    assert "Confirm delete" in detail and 'name="csrfmiddlewaretoken"' in detail
    assert client.get(delete).status_code == 405


def test_questionnaire_forms_show_authoritative_limits(
    client: object, staff_quiz: object
) -> None:
    """Use the same duration, pass mark, and attempt bounds as validation."""
    quiz = staff_quiz
    for name, pk in (("create", quiz.course_id), ("edit", quiz.pk)):
        html = learning_html(client, f"assessments:{name}", (pk,))
        assert "YYYY-MM-DD HH:MM" in html
        assert f"to {MAX_DURATION_MINUTES} minutes" in html
        assert f"to {MAX_PASS_PERCENT} percent" in html
        assert f"to {MAX_ATTEMPTS} attempts" in html


def test_question_rows_and_correct_group_preserve_server_contract(
    client: object, staff_quiz: object
) -> None:
    """Submit labelled rows, reject gaps, and keep correctness out of the paper."""
    quiz = staff_quiz
    url = reverse("assessments:question_add", args=[quiz.pk])
    html = learning_html(client, "assessments:question_add", (quiz.pk,))
    assert "<legend>Correct option:</legend>" in html
    assert all(f'for="id_options_{i - 1}">Option {i}' in html for i in range(1, 7))
    data = {
        "text": "Which route?",
        "marks": 1,
        "options_0": "First",
        "options_2": "Second",
        "correct_option": 2,
    }
    error = client.post(url, data)
    assert b"without gaps" in error.content and b'href="#id_options"' in error.content
    data["options_1"] = data.pop("options_2")
    assert client.post(url, data).status_code == 302
    question = quiz.questions.get()
    assert question.options.get(is_correct=True).text == "Second"
    _assert_staff_correctness_and_freeze(client, quiz, question)


def _assert_staff_correctness_and_freeze(
    client: object, quiz: object, question: object
) -> None:
    """Check frozen authoring and render the same quiz as its trainee."""
    edit = reverse("assessments:question_edit", args=[question.pk])
    assert "<legend>Correct option:</legend>" in learning_html(
        client, "assessments:question_edit", (question.pk,)
    )
    detail = learning_html(client, "assessments:manage_detail", (quiz.pk,))
    delete = reverse("assessments:question_delete", args=[question.pk])
    assert f'<form method="post" action="{delete}">' in detail
    assert "Confirm delete" in detail and 'name="csrfmiddlewaretoken"' in detail
    assert client.get(delete).status_code == 405
    enrollment = EnrollmentFactory(course=quiz.course)
    attempt = AttemptFactory(trainee=enrollment.trainee, questionnaire=quiz)
    rejected = client.post(
        edit,
        {"text": "Edit", "marks": 1, "options": "First\nSecond", "correct_option": 2},
    )
    assert b"frozen after any attempt." in rejected.content
    client.force_login(enrollment.trainee)
    paper = learning_html(client, "assessments:take", (attempt.pk,))
    assert "Correct option" not in paper and "is_correct" not in paper
    assert 'name="correct_option"' not in paper


@pytest.mark.parametrize("attempted", (0, 2, 3))
def test_participation_heat_strip_and_table(
    client: object, staff_quiz: object, attempted: int
) -> None:
    """Show zero-safe stats and a decorative duplicate of the accessible table."""
    quiz = staff_quiz
    for index in range(3):
        enrollment = EnrollmentFactory(course=quiz.course)
        if index < attempted:
            AttemptFactory(
                questionnaire=quiz,
                trainee=enrollment.trainee,
                status="SUBMITTED",
                percent=80,
                passed=index == 0,
            )
    html = learning_html(client, "assessments:participation", (quiz.pk,))
    assert "<caption>Trainee participation</caption>" in html and 'scope="row"' in html
    assert 'class="heat-strip" aria-hidden="true"' in html
    assert ('aria-label="Not attempted"' in html) == (attempted < 3)
    assert ('aria-label="Passed"' in html) == bool(attempted)
    assert ('aria-label="Attempted, not passed"' in html) == bool(attempted)
    assert ("No trainees have attempted" in html) == (attempted == 0)
    assert "0.00%" in html or attempted == 3
    legend = html.split('aria-label="Participation legend">', 1)[1].split("</ul>", 1)[0]
    for cue, label in (
        ("cue-hollow", "Not attempted"),
        ("cue-diagonal", "Attempted, not passed"),
        ("cue-check", "Passed"),
    ):
        assert cue in legend and label in legend


def test_staff_result_discloses_correct_answer_only_to_authorized_staff(
    client: object, staff_quiz: object
) -> None:
    """Retain staff disclosure even while trainee quota remains."""
    quiz = staff_quiz
    question = QuestionFactory(questionnaire=quiz)
    attempt = AttemptFactory(questionnaire=quiz, status="SUBMITTED")
    AnswerFactory(attempt=attempt, question=question)
    html = learning_html(client, "assessments:result", (attempt.pk,))
    assert "Correct option: Choice Alpha" in html and "SUBMITTED" in html
    client.force_login(UserFactory(approved_trainer=True))
    for route, pk in (
        ("manage_detail", quiz.pk),
        ("edit", quiz.pk),
        ("question_add", quiz.pk),
        ("question_edit", question.pk),
        ("participation", quiz.pk),
        ("result", attempt.pk),
        ("course_list", quiz.course_id),
    ):
        assert client.get(reverse(f"assessments:{route}", args=[pk])).status_code == 404
