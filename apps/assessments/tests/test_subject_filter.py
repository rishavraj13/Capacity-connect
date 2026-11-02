"""Prove subject discovery respects the trainee's existing enrollment scope."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import QuestionnaireFactory
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def test_mine_filters_questionnaires_and_departures_by_subject(client: object) -> None:
    """Filter both visible lists without hiding the explicit subject control."""
    user = UserFactory(approved_trainee=True)
    quizzes = QuestionnaireFactory.create_batch(2)
    for quiz in quizzes:
        EnrollmentFactory(trainee=user, course=quiz.course)
    client.force_login(user)
    response = client.get(
        reverse("assessments:mine"), {"subject": quizzes[0].subject_id}
    )
    assert list(response.context["questionnaires"]) == [quizzes[0]]
    assert {row.subject_name for row in response.context["departures"]} == {
        quizzes[0].subject.name
    }
    assert b"Filter by subject" in response.content


@pytest.mark.parametrize("value", ["not-an-id", "999999"])
def test_invalid_subject_is_a_form_error(client: object, value: str) -> None:
    """Never expand enrollment scope for a malformed or foreign subject ID."""
    user = UserFactory(approved_trainee=True)
    client.force_login(user)
    response = client.get(reverse("assessments:mine"), {"subject": value})
    assert response.status_code == 200
    assert response.context["filter_form"].errors["subject"]
    assert not response.context["questionnaires"]


def test_empty_filter_retains_all_enrolled_subjects(client: object) -> None:
    """Keep defaults useful while excluding another trainee's questionnaire."""
    quiz = QuestionnaireFactory()
    own = EnrollmentFactory(course=quiz.course).trainee
    QuestionnaireFactory()
    client.force_login(own)
    response = client.get(reverse("assessments:mine"))
    assert list(response.context["questionnaires"]) == [quiz]
