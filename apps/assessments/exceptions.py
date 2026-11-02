"""Keep assessment rejections recoverable at HTTP boundaries."""

from apps.core.exceptions import CapacityConnectError


class AssessmentRuleError(CapacityConnectError):
    """Reject invalid authoring and attempt transitions without leaking internals."""
