"""Constants and choice enumerations for user accounts."""

from django.db import models


class UserRole(models.TextChoices):
    """Available user roles within the portal."""

    TRAINEE = "TRAINEE", "Trainee"
    TRAINER = "TRAINER", "Trainer"
    ADMIN = "ADMIN", "Admin"


SIGNUP_ROLES: tuple[str, ...] = (
    UserRole.TRAINEE,
    UserRole.TRAINER,
)

ROLE_HOME_URL_NAMES: dict[str, str] = {
    UserRole.TRAINEE: "trainee_home",
    UserRole.TRAINER: "trainer_home",
    UserRole.ADMIN: "admin_panel",
}

ADMIN_USER_PAGE_SIZE: int = 20

STATUS_ALL: str = "all"
STATUS_ACTIVE: str = "active"
STATUS_INACTIVE: str = "inactive"
STATUS_PENDING: str = "pending"

MSG_AWAITING_APPROVAL: str = (
    "Your account is awaiting administrator approval. "
    "You will receive access once approved."
)
MSG_INVALID_CREDENTIALS: str = (
    "Please enter a correct username and password. "
    "Note that both fields may be case-sensitive."
)
MSG_ACCOUNT_DISABLED: str = (
    "This account has been disabled. Please contact portal administration."
)
