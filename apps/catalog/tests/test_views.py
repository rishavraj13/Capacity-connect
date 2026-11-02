"""Verify catalog forms invoke the correct lifecycle services."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.models import Skill, Subject
from apps.catalog.tests.factories import SubjectFactory

pytestmark = pytest.mark.django_db


def test_admin_subject_create_edit(client: Client) -> None:
    """Persist descriptive catalog changes through validated HTTP forms."""
    client.force_login(UserFactory(active_admin=True))
    response = client.post(reverse("catalog:subject_create"), {"name": "Science"})
    assert response.status_code == 302
    subject = Subject.objects.get(name="Science")
    response = client.post(
        reverse("catalog:subject_edit", args=[subject.pk]),
        {"name": "Sciences", "description": "New"},
    )
    assert response.status_code == 302
    subject.refresh_from_db()
    assert subject.name == "Sciences" and subject.description == "New"


def test_admin_skill_create_edit_delete(client: Client) -> None:
    """Route every skill write through its intended service."""
    client.force_login(UserFactory(active_admin=True))
    subject = SubjectFactory()
    response = client.post(
        reverse("catalog:skill_create"), {"name": "Logic", "subject": subject.pk}
    )
    assert response.status_code == 302
    skill = Skill.objects.get(name="Logic")
    response = client.post(
        reverse("catalog:skill_edit", args=[skill.pk]),
        {"name": "Reasoning", "subject": subject.pk},
    )
    assert response.status_code == 302
    skill.refresh_from_db()
    assert skill.name == "Reasoning"
    assert (
        client.post(reverse("catalog:skill_delete", args=[skill.pk])).status_code == 302
    )
    assert not Skill.objects.exists()


def test_admin_subject_activation(client: Client) -> None:
    """Keep subject retirement reversible without deleting history."""
    client.force_login(UserFactory(active_admin=True))
    subject = SubjectFactory()
    for action, state in (("deactivate", False), ("reactivate", True)):
        response = client.post(reverse(f"catalog:subject_{action}", args=[subject.pk]))
        assert response.status_code == 302
        subject.refresh_from_db()
        assert subject.is_active is state
