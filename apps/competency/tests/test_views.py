"""Keep declaration forms ownership-safe and ranking reachable only to Admin."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.competency.models import TrainerCompetency
from apps.competency.tests.factories import CompetencyFactory

pytestmark = pytest.mark.django_db


def test_declaration_and_edit_forms_ignore_forged_owner_fields(client: object) -> None:
    """Persist own declarations while excluding immutable subject/owner updates."""
    user = UserFactory(approved_trainer=True)
    subject = SubjectFactory()
    client.force_login(user)
    assert (
        client.post(
            reverse("competency:add"),
            declaration_data(subject),
        ).status_code
        == 302
    )
    row = TrainerCompetency.objects.get()
    assert row.trainer == user and row.subject == subject
    assert (
        client.post(
            reverse("competency:edit", args=[row.pk]),
            {"subject": 999, "proficiency": 5, "years_experience": 9},
        ).status_code
        == 302
    )
    row.refresh_from_db()
    assert row.subject == subject and row.proficiency == 5


def test_admin_subject_picker_shows_rankings_and_retired_subjects(
    client: object,
) -> None:
    """Keep retired declarations discoverable without permitting Admin edits."""
    row = CompetencyFactory(
        subject__is_active=False, trainer__first_name="RankedTrainer"
    )
    client.force_login(UserFactory(active_admin=True))
    response = client.get(reverse("competency:ranking"), {"subject": row.subject_id})
    assert response.status_code == 200 and b"RankedTrainer" in response.content
    assert response.context["ranking"][0].trainer_id == row.trainer_id
    assert (
        client.get(reverse("competency:ranking"), {"subject": "invalid"}).status_code
        == 200
    )


def declaration_data(subject: object) -> dict:
    """Include forged ownership alongside valid public declaration input."""
    return {
        "subject": subject.pk,
        "proficiency": 4,
        "years_experience": 8,
        "trainer": 999,
    }
