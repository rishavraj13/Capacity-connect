"""Declare every course URL/method against seven ownership-aware actors."""

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
from apps.courses.tests.factories import CourseFactory, EnrollmentFactory, ModuleFactory

COURSE_ROUTES = (
    "list",
    "detail",
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
    "my_courses",
    "station_map",
    "participants",
)
POST_ACTIONS = {
    "publish",
    "unpublish",
    "module_delete",
    "enroll",
    "drop",
    "complete_module",
}
READ_ROUTES = {"list", "detail", "my_courses", "station_map", "participants"}
TRAINEE_ROUTES = {"enroll", "drop", "complete_module", "my_courses", "station_map"}


def _method_status(name: str, method: str) -> int:
    """Describe HTTP method behavior separately from actor/object authorization."""
    if name in POST_ACTIONS and method == "GET":
        return 405
    if name in READ_ROUTES and method == "POST":
        return 405
    return 302 if name in POST_ACTIONS else 200


def expected_status(actor: str, name: str, method: str) -> int:
    """Keep expected permissions independent of production role decorators."""
    if actor in {"anonymous", "inactive"}:
        return 302
    if actor == "unapproved":
        return 403
    status = _method_status(name, method)
    if name in {"list", "detail"}:
        return status
    if name in TRAINEE_ROUTES:
        return status if actor == "trainee" else 403
    if actor not in {"trainer_owner", "trainer_other", "admin"}:
        return 403
    if status == 405:
        return status
    return 404 if actor == "trainer_other" and name != "create" else status


PERMISSION_MATRIX = [
    (actor, f"courses:{name}", method, expected_status(actor, name, method))
    for name in COURSE_ROUTES
    for actor in OWNERSHIP_ACTORS
    for method in ("GET", "POST")
]


def matrix_url(name: str, user: object, actor: str) -> str:
    """Associate fixture ownership with the current trainee or owner-trainer actor."""
    course = CourseFactory(
        is_published=True, **({"trainer": user} if actor == "trainer_owner" else {})
    )
    enrollment = EnrollmentFactory(
        course=course, **({"trainee": user} if actor == "trainee" else {})
    )
    module = ModuleFactory(course=course, order=1)
    if name in {"list", "create", "my_courses", "station_map"}:
        args = []
    elif name == "complete_module":
        args = [enrollment.pk, module.pk]
    elif name == "drop":
        args = [enrollment.pk]
    else:
        args = [module.pk if name in {"module_edit", "module_delete"} else course.pk]
    return reverse(f"courses:{name}", args=args)


@pytest.mark.django_db
@pytest.mark.parametrize("row", PERMISSION_MATRIX, ids=matrix_id)
def test_course_permission_matrix(client: Client, row: tuple) -> None:
    """Exercise all new course URLs through the reusable matrix machinery."""
    user = actor_user(row[0])
    url = matrix_url(row[1].split(":")[1], user, row[0])
    assert_matrix_case(client, row, MatrixRequest(url, user=user))
