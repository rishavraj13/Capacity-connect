"""Create demo applicants through account services and the superuser manager."""

from django.contrib.auth import get_user_model, password_validation

from apps.accounts.constants import UserRole
from apps.accounts.services import approve_user, register_user, reject_user
from apps.core.demo_constants import (
    ADMIN_USERNAME,
    APPROVED_TRAINEES,
    PENDING_TRAINEES,
    TRAINEE_NAMES,
    TRAINER_NAMES,
)
from apps.core.demo_data import DemoGraph


def _admin(password: str) -> object:
    """Use Django's real superuser workflow for the one demo Admin."""
    users = get_user_model().objects
    existing = users.filter(username=ADMIN_USERNAME).first()
    if existing:
        return existing
    return users.create_superuser(
        username=ADMIN_USERNAME,
        email="demo_admin@example.test",
        password=password,
        first_name="Rohan",
        last_name="Menon",
    )


def _applicant(name: tuple, role: str, state: str, context: tuple) -> object:
    """Reuse namespace accounts without resetting existing data on reruns."""
    admin, password = context
    first, last = name
    username = f"demo_{role.lower()}_{first.lower()}"
    existing = get_user_model().objects.filter(username=username).first()
    if existing:
        return existing
    user = register_user(
        {
            "username": username,
            "email": username + "@example.test",
            "first_name": first,
            "last_name": last,
            "password": password,
            "role": role,
        }
    )
    if state == "approved":
        approve_user(user, admin)
    elif state == "rejected":
        reject_user(user, admin)
    return user


def demo_accounts(password: str) -> DemoGraph:
    """Create one Admin, three approved trainers and twelve mixed-state trainees."""
    password_validation.validate_password(password)
    admin = _admin(password)
    context = (admin, password)
    trainers = tuple(
        _applicant(name, UserRole.TRAINER, "approved", context)
        for name in TRAINER_NAMES
    )
    trainees = tuple(
        _applicant(name, UserRole.TRAINEE, _state(index), context)
        for index, name in enumerate(TRAINEE_NAMES)
    )
    return DemoGraph(admin, trainers, trainees)


def _state(index: int) -> str:
    """Keep pending/rejected applicant examples separate from approved learners."""
    if index < APPROVED_TRAINEES:
        return "approved"
    return "pending" if index < APPROVED_TRAINEES + PENDING_TRAINEES else "rejected"
