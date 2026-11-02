"""Declare every B4 URL/method across seven ownership-aware actor types."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.assessments.constants import AttemptStatus
from apps.assessments.tests.factories import (
    AttemptFactory,
    QuestionFactory,
    QuestionnaireFactory,
)
from apps.core.tests.matrix import (
    OWNERSHIP_ACTORS,
    MatrixRequest,
    actor_user,
    assert_matrix_case,
    matrix_id,
)
from apps.courses.tests.factories import CourseFactory, EnrollmentFactory

ROUTES = (
    "course_list",
    "create",
    "manage_detail",
    "edit",
    "delete",
    "question_add",
    "question_edit",
    "question_delete",
    "participation",
    "mine",
    "detail",
    "start",
    "take",
    "result",
    "history",
)
STAFF_ROUTES = {
    "course_list",
    "create",
    "manage_detail",
    "edit",
    "delete",
    "question_add",
    "question_edit",
    "question_delete",
    "participation",
}
POST_ONLY = {"delete", "question_delete", "start"}
FORMS = {"create", "edit", "question_add", "question_edit", "take"}


def expected_status(actor: str, name: str, method: str) -> int:
    """Keep role, method and object expectations independent of view decorators."""
    if actor in {"anonymous", "inactive"}:
        return 302
    if actor == "unapproved":
        return 403
    if name == "result":
        return 405 if method == "POST" else (404 if actor == "trainer_other" else 200)
    if name in STAFF_ROUTES:
        if actor not in {"trainer_owner", "trainer_other", "admin"}:
            return 403
    elif actor != "trainee":
        return 403
    return object_status(actor, name, method)


def object_status(actor: str, name: str, method: str) -> int:
    """Check method before object scope as the decorated endpoints do."""
    if name in POST_ONLY and method == "GET":
        return 405
    if name not in POST_ONLY | FORMS and method == "POST":
        return 405
    if name in STAFF_ROUTES and actor == "trainer_other":
        return 404
    return 302 if method == "POST" and name in POST_ONLY | {"take"} else 200


PERMISSION_MATRIX = [
    (actor, f"assessments:{name}", method, expected_status(actor, name, method))
    for name in ROUTES
    for actor in OWNERSHIP_ACTORS
    for method in ("GET", "POST")
]


def matrix_url(name: str, user: object, actor: str) -> str:
    """Use actor-matched owners without weakening shared matrix machinery."""
    course = CourseFactory(
        is_published=True, **({"trainer": user} if actor == "trainer_owner" else {})
    )
    quiz = QuestionnaireFactory(course=course)
    question = QuestionFactory(questionnaire=quiz)
    trainee = EnrollmentFactory(
        course=course, **({"trainee": user} if actor == "trainee" else {})
    ).trainee
    if name in {"mine", "history"}:
        args = []
    elif name in {"take", "result"}:
        args = [matrix_attempt(name, quiz, trainee).pk]
    else:
        pk = (
            course.pk
            if name in {"course_list", "create"}
            else (
                question.pk if name in {"question_edit", "question_delete"} else quiz.pk
            )
        )
        args = [pk]
    return reverse(f"assessments:{name}", args=args)


@pytest.mark.django_db
@pytest.mark.parametrize("row", PERMISSION_MATRIX, ids=matrix_id)
def test_assessment_permission_matrix(client: Client, row: tuple) -> None:
    """Exercise every new URL with both methods and the shared ownership runner."""
    user = actor_user(row[0])
    assert_matrix_case(
        client,
        row,
        MatrixRequest(matrix_url(row[1].split(":")[1], user, row[0]), user=user),
    )


def matrix_attempt(name: str, quiz: object, trainee: object) -> object:
    """Separate final/open attempt fixtures from URL argument selection."""
    status = AttemptStatus.SUBMITTED if name == "result" else AttemptStatus.IN_PROGRESS
    return AttemptFactory(questionnaire=quiz, trainee=trainee, status=status)
