"""Expose course failures as recoverable domain feedback."""

from apps.core.exceptions import CapacityConnectError


class CourseRuleError(CapacityConnectError):
    """Reject course or module writes that violate workflow rules."""


class EnrollmentRuleError(CapacityConnectError):
    """Reject invalid enrollment or sequential-progress transitions."""
