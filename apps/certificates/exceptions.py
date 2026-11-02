"""Separate retryable generation failures from completion eligibility."""

from apps.core.exceptions import CapacityConnectError


class CertificateGenerationError(CapacityConnectError):
    """Preserve learning writes when a certificate cannot be produced."""


class CertificateRuleError(CapacityConnectError):
    """Refuse direct issuance before a qualifying completion."""
