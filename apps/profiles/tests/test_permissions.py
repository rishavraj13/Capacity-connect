"""Declare profile URL access including object ownership and private file kinds."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.tests.matrix import (
    ACTOR_TRAITS,
    MatrixRequest,
    actor_user,
    assert_matrix_case,
    matrix_id,
)
from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    QualificationFactory,
    TraineeProfileFactory,
    TrainerProfileFactory,
    WorkExperienceFactory,
    photo_upload,
)

PROFILE_ROUTES = {
    "profile_list": "all",
    "account_edit": "all",
    "trainee_detail": "all",
    "trainer_detail": "all",
    "trainee_edit": "trainee",
    "trainer_edit": "trainer",
    "qualification_create": "trainee",
    "qualification_edit": "trainee",
    "qualification_delete": "trainee",
    "experience_create": "trainee",
    "experience_edit": "trainee",
    "experience_delete": "trainee",
    "certificate_create": "trainee",
    "certificate_edit": "trainee",
    "certificate_delete": "trainee",
    "private_file_trainee": "all",
    "private_file_trainer": "all",
    "private_file_certificate": "all",
}
READ_ONLY = {
    "profile_list",
    "trainee_detail",
    "trainer_detail",
    "private_file_trainee",
    "private_file_trainer",
    "private_file_certificate",
}


def expected_status(actor: str, name: str, method: str) -> int:
    """Describe access independently of the view implementation."""
    if actor in {"anonymous", "rejected_user"}:
        return 302
    required = PROFILE_ROUTES[name]
    if (
        actor == "unapproved_user"
        or required != "all"
        and actor != f"approved_{required}"
    ):
        return 403
    if name.endswith("_delete"):
        return 405 if method == "GET" else 302
    if name in READ_ONLY:
        if method == "POST":
            return 405
        private = name in {
            "trainee_detail",
            "private_file_trainee",
            "private_file_certificate",
        }
        return 404 if private and actor == "approved_trainer" else 200
    return 302 if name == "trainee_edit" and method == "POST" else 200


PERMISSION_MATRIX = [
    (actor, f"profiles:{name}", method, expected_status(actor, name, method))
    for name in PROFILE_ROUTES
    for actor in ("anonymous", *ACTOR_TRAITS)
    for method in ("GET", "POST")
]


def file_url(kind: str, trainee: object, trainer: object, certificate: object) -> str:
    """Keep file fixture routing separate from profile object construction."""
    pk = {"trainee": trainee.pk, "trainer": trainer.pk, "certificate": certificate.pk}[
        kind
    ]
    return reverse("profiles:private_file", args=[kind, pk])


def matrix_target(name: str, user: object) -> str:
    """Build private fixtures owned by the supplied trainee when appropriate."""
    own = {"user": user} if user and user.role == "TRAINEE" else {}
    trainee = TraineeProfileFactory(photo=photo_upload(), **own)
    trainer = TrainerProfileFactory(photo=photo_upload())
    records = {
        "qualification": QualificationFactory(profile=trainee),
        "experience": WorkExperienceFactory(profile=trainee),
        "certificate": ExternalCertificateFactory(profile=trainee),
    }
    if name.startswith("private_file_"):
        kind = name.removeprefix("private_file_")
        return file_url(kind, trainee, trainer, records["certificate"])
    if name.endswith("_detail"):
        return reverse(
            f"profiles:{name}",
            args=[trainee.pk if name == "trainee_detail" else trainer.pk],
        )
    slug, _, action = name.partition("_")
    args = (
        [records[slug].pk] if slug in records and action in {"edit", "delete"} else []
    )
    return reverse(f"profiles:{name}", args=args)


@pytest.mark.django_db
@pytest.mark.parametrize("row", PERMISSION_MATRIX, ids=matrix_id)
def test_profile_permission_matrix(client: Client, row: tuple) -> None:
    """Exercise every new profile URL across six actors and both methods."""
    user = actor_user(row[0])
    url = matrix_target(row[1].split(":")[1], user)
    assert_matrix_case(client, row, MatrixRequest(url, user=user))
