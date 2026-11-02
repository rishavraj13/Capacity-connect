"""Exercise certificate uniqueness and percent protection through direct writes."""

import pytest
from django.db import IntegrityError, transaction

from apps.certificates.tests.factories import CertificateFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("percent", [-1, 101])
def test_certificate_percent_constraint(percent: int) -> None:
    """Reject invalid aggregates even if issuance is bypassed."""
    with pytest.raises(IntegrityError), transaction.atomic():
        CertificateFactory(average_percent=percent)


@pytest.mark.parametrize("field", ["enrollment", "certificate_id"])
def test_certificate_unique_enrollment_and_identifier(field: str) -> None:
    """Protect exactly-once issuance and globally unique public identifiers."""
    row = CertificateFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        CertificateFactory(**{field: getattr(row, field)})
