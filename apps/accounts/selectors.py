"""Database selector functions providing optimized querysets for accounts."""

from django.db.models import QuerySet

from apps.accounts.constants import (
    STATUS_ACTIVE,
    STATUS_ALL,
    STATUS_INACTIVE,
    STATUS_PENDING,
    UserRole,
)
from apps.accounts.models import User


def pending_users() -> QuerySet[User]:
    """Retrieve all active users currently awaiting administrator approval."""
    return User.objects.filter(
        is_approved=False,
        is_active=True,
    ).order_by("-date_joined")


def users_filtered(
    role: str | None = None,
    status: str | None = None,
) -> QuerySet[User]:
    """Filter user accounts by role and approval/active status flags."""
    queryset: QuerySet[User] = User.objects.all().order_by("-date_joined")
    if role and role != STATUS_ALL and role in UserRole.values:
        queryset = queryset.filter(role=role)
    if status == STATUS_PENDING:
        queryset = queryset.filter(is_approved=False, is_active=True)
    elif status == STATUS_ACTIVE:
        queryset = queryset.filter(is_approved=True, is_active=True)
    elif status == STATUS_INACTIVE:
        queryset = queryset.filter(is_active=False)
    return queryset


def email_in_use(email: str, excluding_user_id: int) -> bool:
    """Share case-insensitive account collision reads with profile forms."""
    return (
        User.objects.exclude(pk=excluding_user_id).filter(email__iexact=email).exists()
    )
