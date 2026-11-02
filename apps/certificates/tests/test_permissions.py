"""Declare every new B5 route across ownership-aware actors and both methods."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.core.tests.matrix import (
    OWNERSHIP_ACTORS,
    MatrixRequest,
    actor_user,
    assert_matrix_case,
    matrix_id,
    public_permission_rows,
)
from apps.courses.tests.factories import CourseFactory, EnrollmentFactory
from apps.feedback.tests.factories import FeedbackFactory
from apps.library.tests.factories import ResourceFactory

PRIVATE_ROUTES = (
    "feedback:mine",
    "feedback:course_submit",
    "feedback:resource_submit",
    "feedback:delete",
    "feedback:course_summary",
    "feedback:resource_summary",
    "certificates:mine",
    "certificates:download",
)
PUBLIC_ROUTES = ("certificates:verify_form", "certificates:verify")


def expected(actor: str, name: str, method: str) -> int:
    """Keep role and method expectations explicit rather than inspecting views."""
    if actor in {"anonymous", "inactive"}:
        return 302
    if actor == "unapproved":
        return 403
    staff = name.endswith("summary") or name == "certificates:download"
    allowed = {"trainer_owner", "trainer_other", "admin"} if staff else {"trainee"}
    if name == "certificates:download":
        allowed.add("trainee")
    if actor not in allowed:
        return 403
    return object_status(actor, name, method)


def object_status(actor: str, name: str, method: str) -> int:
    """Apply method guards before staff ownership lookups."""
    if name == "feedback:delete":
        return 405 if method == "GET" else 302
    if name.endswith("submit"):
        return 200
    if method == "POST":
        return 405
    return 404 if actor == "trainer_other" else 200


PERMISSION_MATRIX = [
    (actor, name, method, expected(actor, name, method))
    for name in PRIVATE_ROUTES
    for actor in OWNERSHIP_ACTORS
    for method in ("GET", "POST")
]
PERMISSION_MATRIX += [
    row for name in PUBLIC_ROUTES for row in public_permission_rows(name)
]


def matrix_url(name: str, user: object, actor: str) -> str:
    """Build real owned targets without weakening the shared matrix runner."""
    course = CourseFactory(**({"trainer": user} if actor == "trainer_owner" else {}))
    trainee = user if actor == "trainee" else UserFactory(approved_trainee=True)
    enrollment = EnrollmentFactory(course=course, trainee=trainee)
    resource = ResourceFactory(
        course=course, subject=course.subject, trainer=course.trainer, is_published=True
    )
    args = []
    if name == "certificates:verify":
        args = [CertificateFactory(enrollment=enrollment).certificate_id]
    elif name == "certificates:download":
        args = [CertificateFactory(enrollment=enrollment).pk]
    elif name == "feedback:delete":
        args = [FeedbackFactory(author=trainee, course=course).pk]
    elif "course_" in name:
        args = [course.pk]
    elif "resource_" in name:
        args = [resource.pk]
    return reverse(name, args=args)


@pytest.mark.django_db
@pytest.mark.parametrize("row", PERMISSION_MATRIX, ids=matrix_id)
def test_b5_permission_matrix(client: object, row: tuple) -> None:
    """Exercise anonymous public rows through the same runner as private routes."""
    user = actor_user(row[0])
    assert_matrix_case(
        client, row, MatrixRequest(matrix_url(row[1], user, row[0]), user=user)
    )
