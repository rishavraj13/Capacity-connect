"""Translate invalid declarations to shared form feedback."""

from apps.core.exceptions import CapacityConnectError


class CompetencyRuleError(CapacityConnectError):
    """Reject invalid or unauthorized self-declarations without a 500."""
