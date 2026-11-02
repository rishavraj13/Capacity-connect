"""Require CSRF on every assessment authoring/start/submit POST URL."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory

WRITE_ROUTES = (
    "create",
    "edit",
    "delete",
    "question_add",
    "question_edit",
    "question_delete",
    "start",
    "take",
)


@pytest.mark.django_db
@pytest.mark.parametrize("name", WRITE_ROUTES)
def test_assessment_post_routes_require_csrf(name: str) -> None:
    """Reject forged state-changing requests before ownership evaluation."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(UserFactory(active_admin=True))
    assert client.post(reverse(f"assessments:{name}", args=[1])).status_code == 403
