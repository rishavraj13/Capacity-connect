"""Present authoring failures through shared form/action feedback."""

from apps.core.exceptions import CapacityConnectError


class AnnouncementRuleError(CapacityConnectError):
    """Reject invalid Admin publication actions without exposing database errors."""
