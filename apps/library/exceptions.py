"""Expose resource failures without HTTP or storage details."""

from apps.core.exceptions import CapacityConnectError


class ResourceRuleError(CapacityConnectError):
    """Reject invalid resource ownership, associations and uploads."""
