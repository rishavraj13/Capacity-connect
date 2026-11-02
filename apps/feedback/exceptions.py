"""Give feedback failures shared form/action feedback."""

from apps.core.exceptions import CapacityConnectError


class FeedbackRuleError(CapacityConnectError):
    """Explain a rejected opinion without leaking database failures."""
