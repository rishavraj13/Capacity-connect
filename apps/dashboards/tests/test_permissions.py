"""Exercise all B6 routes through the shared actor/method matrix."""

import pytest
from django.urls import reverse

from apps.announcements.tests.factories import AnnouncementFactory
from apps.competency.tests.factories import CompetencyFactory
from apps.core.tests.matrix import (
    OWNERSHIP_ACTORS,
    MatrixRequest,
    actor_user,
    assert_matrix_case,
    matrix_id,
    public_permission_rows,
)

TRAINER_ROUTES = (
    "competency:mine",
    "competency:add",
    "competency:edit",
    "competency:remove",
    "dashboards:trainer",
)
ADMIN_ROUTES = (
    "competency:ranking",
    "announcements:manage",
    "announcements:create",
    "announcements:edit",
    "announcements:publish",
    "announcements:unpublish",
    "announcements:delete",
    "dashboards:admin",
)
STATE_ROUTES = {
    "competency:remove",
    "announcements:publish",
    "announcements:unpublish",
    "announcements:delete",
}
FORM_ROUTES = {
    "competency:add",
    "competency:edit",
    "announcements:create",
    "announcements:edit",
}


def expected(actor: str, name: str, method: str) -> int:
    """Declare role/method/object outcomes independently of view decorators."""
    if actor in {"anonymous", "inactive"}:
        return 302
    if actor == "unapproved":
        return 403
    allowed = (
        actor in {"trainer_owner", "trainer_other"}
        if name in TRAINER_ROUTES
        else actor == "admin"
    )
    if not allowed:
        return 403
    if method == "GET" and name in STATE_ROUTES:
        return 405
    if method == "POST" and name not in STATE_ROUTES | FORM_ROUTES:
        return 405
    if actor == "trainer_other" and name in {"competency:edit", "competency:remove"}:
        return 404
    return 302 if method == "POST" and name in STATE_ROUTES else 200


PERMISSION_MATRIX = [
    (actor, name, method, expected(actor, name, method))
    for name in TRAINER_ROUTES + ADMIN_ROUTES
    for actor in OWNERSHIP_ACTORS
    for method in ("GET", "POST")
]
PERMISSION_MATRIX += public_permission_rows("announcements:home")


def matrix_url(name: str, user: object, actor: str) -> str:
    """Build actor-matched owned declarations and independent Admin announcements."""
    if name in {"competency:edit", "competency:remove"}:
        row = CompetencyFactory(
            **({"trainer": user} if actor == "trainer_owner" else {})
        )
        return reverse(name, args=[row.pk])
    if name in {
        "announcements:edit",
        "announcements:publish",
        "announcements:unpublish",
        "announcements:delete",
    }:
        row = AnnouncementFactory()
        return reverse(name, args=[row.pk])
    return reverse(name)


@pytest.mark.django_db
@pytest.mark.parametrize("row", PERMISSION_MATRIX, ids=matrix_id)
def test_b6_permission_matrix(client: object, row: tuple) -> None:
    """Apply the same private/public runner to all fourteen new B6 routes."""
    user = actor_user(row[0])
    assert_matrix_case(
        client, row, MatrixRequest(matrix_url(row[1], user, row[0]), user=user)
    )
