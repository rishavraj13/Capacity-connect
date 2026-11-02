"""Domain service functions for user lifecycle and administrative actions."""

from typing import Any

from apps.accounts.constants import SIGNUP_ROLES, UserRole
from apps.accounts.models import User
from apps.accounts.selectors import approved_users
from apps.core.exceptions import (
    InvalidRoleError,
    LastAdminProtectionError,
    SelfModificationError,
    UserManagementError,
)


def _assert_not_self(
    target_user: User,
    admin_user: User,
    action_name: str,
) -> None:
    """Ensure administrator cannot perform prohibited self-modifications."""
    if target_user.pk == admin_user.pk:
        raise SelfModificationError(
            f"Administrators cannot {action_name} their own account."
        )


def _assert_not_last_active_admin(target_user: User) -> None:
    """Ensure portal always retains at least one active administrator."""
    if target_user.role == UserRole.ADMIN and target_user.is_active:
        active_admin_count: int = User.objects.filter(
            role=UserRole.ADMIN,
            is_active=True,
        ).count()
        if active_admin_count <= 1:
            raise LastAdminProtectionError(
                "Cannot reject or demote the last active administrator."
            )


def register_user(data: dict[str, Any]) -> User:
    """Create a new unapproved user restricted to trainee or trainer roles."""
    role: str = data.get("role", "")
    if role not in SIGNUP_ROLES:
        raise InvalidRoleError("Registration is limited to TRAINEE or TRAINER.")
    email: str = data["email"].strip().lower()
    return User.objects.create_user(
        username=data["username"].strip(),
        email=email,
        password=data["password"],
        first_name=data.get("first_name", "").strip(),
        last_name=data.get("last_name", "").strip(),
        role=role,
        is_approved=False,
    )


def approve_user(target_user: User, admin_user: User) -> User:
    """Grant portal access by approving an existing user account."""
    target_user.is_approved = True
    target_user.save(update_fields=["is_approved"])
    return target_user


def reject_user(target_user: User, admin_user: User) -> User:
    """Deactivate user account representing rejected application status."""
    _assert_not_self(target_user, admin_user, "reject")
    _assert_not_last_active_admin(target_user)
    target_user.is_active = False
    target_user.is_approved = False
    target_user.save(update_fields=["is_active", "is_approved"])
    return target_user


def change_role(target_user: User, new_role: str, admin_user: User) -> User:
    """Update assigned portal role respecting self-demotion and safety rules."""
    if new_role not in UserRole.values:
        raise InvalidRoleError(f"Invalid portal role specified: {new_role}.")
    if target_user.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
        _assert_not_self(target_user, admin_user, "demote")
        _assert_not_last_active_admin(target_user)
    target_user.role = new_role
    target_user.save(update_fields=["role"])
    return target_user


def require_approved_role(user: User, roles: tuple[str, ...]) -> User:
    """Recheck persisted eligibility rather than trusting a stale role object."""
    for role in roles:
        current = approved_users(role).filter(pk=user.pk).first()
        if current:
            return current
    raise UserManagementError(
        "An active approved account with the required role is needed."
    )


def require_owner_or_admin(actor: User, owner_id: int) -> User:
    """Share the ownership rule between course and resource service writes."""
    current = require_approved_role(actor, (UserRole.TRAINER, UserRole.ADMIN))
    if current.role != UserRole.ADMIN and current.pk != owner_id:
        raise UserManagementError(
            "Only the owner or an administrator may manage this record."
        )
    return current


def assigned_trainer(actor: User, data: dict, current: User | None = None) -> User:
    """Set trainer ownership automatically except for explicit Admin assignment."""
    actor = require_approved_role(actor, (UserRole.TRAINER, UserRole.ADMIN))
    trainer = actor if actor.role == UserRole.TRAINER else data.get("trainer", current)
    if trainer is None:
        raise UserManagementError("Select an eligible trainer.")
    return require_approved_role(trainer, (UserRole.TRAINER,))
