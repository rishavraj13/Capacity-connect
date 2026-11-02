"""Read demo evidence without changing any existing record on an idempotent rerun."""

from django.apps import apps

from apps.accounts.models import User
from apps.announcements.models import Announcement
from apps.core.demo_constants import ADMIN_USERNAME, DEMO_MARKER


def demo_exists() -> bool:
    """Use the final service-created notice as the completed seed marker."""
    return Announcement.objects.filter(
        title=DEMO_MARKER, created_by__username=ADMIN_USERNAME
    ).exists()


def demo_summary() -> dict:
    """Provide reviewable global row counts and non-secret demo login identities."""
    counts = {model._meta.label: model.objects.count() for model in apps.get_models()}
    users = User.objects.filter(username__startswith="demo_").order_by(
        "role", "username"
    )
    logins = tuple(
        (
            user.username,
            user.role,
            "rejected"
            if not user.is_active
            else ("approved" if user.is_approved else "pending"),
        )
        for user in users
    )
    return {"counts": counts, "logins": logins}
