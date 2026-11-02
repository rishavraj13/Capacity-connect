"""Declare every resource URL/method against seven ownership-aware actors."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.tests.matrix import (
    OWNERSHIP_ACTORS,
    MatrixRequest,
    actor_user,
    assert_matrix_case,
    matrix_id,
)
from apps.library.tests.factories import ResourceFactory

RESOURCE_ROUTES = (
    "list",
    "detail",
    "create",
    "edit",
    "delete",
    "publish",
    "unpublish",
    "download",
)
POST_ACTIONS = {"delete", "publish", "unpublish"}
READ_ROUTES = {"list", "detail", "download"}


def expected_status(actor: str, name: str, method: str) -> int:
    """Describe visibility and management contracts independently of the view code."""
    if actor in {"anonymous", "inactive"}:
        return 302
    if actor == "unapproved":
        return 403
    if name in READ_ROUTES:
        return 200 if method == "GET" else 405
    if actor not in {"trainer_owner", "trainer_other", "admin"}:
        return 403
    if name in POST_ACTIONS and method == "GET":
        return 405
    if actor == "trainer_other" and name != "create":
        return 404
    return 302 if name in POST_ACTIONS else 200


PERMISSION_MATRIX = [
    (actor, f"library:{name}", method, expected_status(actor, name, method))
    for name in RESOURCE_ROUTES
    for actor in OWNERSHIP_ACTORS
    for method in ("GET", "POST")
]


@pytest.mark.django_db
@pytest.mark.parametrize("row", PERMISSION_MATRIX, ids=matrix_id)
def test_resource_permission_matrix(client: Client, row: tuple) -> None:
    """Use owner-specific fixtures without changing the shared role runner."""
    user = actor_user(row[0])
    resource = ResourceFactory(
        is_published=True, **({"trainer": user} if row[0] == "trainer_owner" else {})
    )
    name = row[1].split(":")[1]
    url = reverse(row[1], args=[] if name in {"list", "create"} else [resource.pk])
    assert_matrix_case(client, row, MatrixRequest(url, user=user))
