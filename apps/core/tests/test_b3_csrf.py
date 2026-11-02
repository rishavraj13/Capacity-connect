"""Require CSRF on every B3 form and state-changing POST route."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory

COURSE_WRITES = (
    "create",
    "edit",
    "publish",
    "unpublish",
    "module_add",
    "module_edit",
    "module_delete",
    "enroll",
    "drop",
    "complete_module",
)
RESOURCE_WRITES = ("create", "edit", "delete", "publish", "unpublish")
POST_URLS = [f"courses:{name}" for name in COURSE_WRITES] + [
    f"library:{name}" for name in RESOURCE_WRITES
]


@pytest.mark.django_db
@pytest.mark.parametrize("name", POST_URLS)
def test_b3_post_routes_require_csrf(name: str) -> None:
    """Reject forged writes before any ownership or business-rule evaluation."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(UserFactory(active_admin=True))
    args = (
        []
        if name.endswith(":create")
        else ([1, 1] if name == "courses:complete_module" else [1])
    )
    assert client.post(reverse(name, args=args)).status_code == 403
