"""Share actor setup and assertions so phases only declare permission rows."""

from dataclasses import dataclass, field

from django.test import Client

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory

ACTOR_TRAITS = {
    "approved_trainee": "approved_trainee",
    "approved_trainer": "approved_trainer",
    "approved_admin": "active_admin",
    "unapproved_user": "pending_trainee",
    "rejected_user": "rejected_user",
}


def actor_user(actor: str) -> User | None:
    """Create a consistent persona for permission checks in every app."""
    trait = ACTOR_TRAITS.get(actor)
    return UserFactory(**{trait: True}) if trait else None


def matrix_id(row: tuple) -> str:
    """Expose actor, URL and method in failing test identifiers."""
    return "-".join(row[:3])


@dataclass
class MatrixRequest:
    """Allow object permission tests to supply the owner used by their fixtures."""

    url: str
    data: dict = field(default_factory=dict)
    user: User | None = None


def assert_matrix_case(client: Client, row: tuple, request: MatrixRequest) -> None:
    """Exercise a declared contract using the fixture's actor when supplied."""
    actor, _, method, expected = row
    user = request.user if request.user is not None else actor_user(actor)
    if user:
        client.force_login(user)
    response = getattr(client, method.lower())(request.url, data=request.data)
    assert response.status_code == expected
    response.close()
