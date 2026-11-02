"""Require CSRF tokens on every new form and state-changing POST endpoint."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.test_permissions import CATALOG_ROUTES
from apps.profiles.tests.test_permissions import PROFILE_ROUTES

POST_URLS = [f"catalog:{name}" for name in CATALOG_ROUTES if name != "subject_list"] + [
    f"profiles:{name}"
    for name in PROFILE_ROUTES
    if not name.startswith("private_file")
    and name not in {"profile_list", "trainee_detail", "trainer_detail"}
]


@pytest.mark.django_db
@pytest.mark.parametrize("name", POST_URLS)
def test_new_post_routes_enforce_csrf(name: str) -> None:
    """Reject forged writes before role or object processing."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(UserFactory(active_admin=True))
    has_pk = name.split(":")[1] in {
        "subject_edit",
        "subject_deactivate",
        "subject_reactivate",
        "skill_edit",
        "skill_delete",
        "qualification_edit",
        "qualification_delete",
        "experience_edit",
        "experience_delete",
        "certificate_edit",
        "certificate_delete",
    }
    url = reverse(name, args=[1] if has_pk else [])
    assert client.post(url).status_code == 403
