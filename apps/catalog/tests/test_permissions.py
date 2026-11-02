"""Declare every catalog URL and method against all six portal actors."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.catalog.tests.factories import SkillFactory, SubjectFactory
from apps.core.tests.matrix import (
    ACTOR_TRAITS,
    MatrixRequest,
    assert_matrix_case,
    matrix_id,
)

CATALOG_ROUTES = {
    "subject_list": None,
    "subject_create": None,
    "subject_edit": "subject",
    "subject_deactivate": "subject",
    "subject_reactivate": "subject",
    "skill_create": None,
    "skill_edit": "skill",
    "skill_delete": "skill",
}
POST_ACTIONS = {"subject_deactivate", "subject_reactivate", "skill_delete"}


def expected_status(actor: str, name: str, method: str) -> int:
    """Express the catalog access contract separately from production decorators."""
    if actor in {"anonymous", "rejected_user"}:
        return 302
    if actor == "unapproved_user":
        return 403
    if name != "subject_list" and actor != "approved_admin":
        return 403
    if name in POST_ACTIONS:
        return 405 if method == "GET" else 302
    return 405 if name == "subject_list" and method == "POST" else 200


PERMISSION_MATRIX = [
    (actor, f"catalog:{name}", method, expected_status(actor, name, method))
    for name in CATALOG_ROUTES
    for actor in ("anonymous", *ACTOR_TRAITS)
    for method in ("GET", "POST")
]


@pytest.mark.django_db
@pytest.mark.parametrize("row", PERMISSION_MATRIX, ids=matrix_id)
def test_catalog_permission_matrix(client: Client, row: tuple) -> None:
    """Exercise the full route contract using the shared matrix runner."""
    subject = SubjectFactory()
    skill = SkillFactory(subject=subject)
    name = row[1].split(":")[1]
    target = {"subject": subject.pk, "skill": skill.pk}.get(CATALOG_ROUTES[name])
    url = reverse(row[1], args=[target] if target else [])
    assert_matrix_case(client, row, MatrixRequest(url))
