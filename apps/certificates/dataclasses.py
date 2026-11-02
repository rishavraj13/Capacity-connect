"""Freeze the certificate renderer's entire external input."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CertificateData:
    """Make PDF generation pure and preserve issued names in the stored bytes."""

    trainee_name: str
    course_title: str
    trainer_name: str
    signatory_name: str
    signatory_title: str
    certificate_id: str
    issued_on: date
    average_percent: Decimal
    grade: str
    verification_url: str


@dataclass(frozen=True, slots=True)
class Verification:
    """Expose only the public fields authorized for certificate lookup."""

    certificate_id: str
    trainee_name: str
    course_title: str
    issued_on: date
