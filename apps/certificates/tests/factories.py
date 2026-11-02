"""Build stored completion records with temporary private storage."""

from datetime import date
from decimal import Decimal

import factory
from django.core.files.base import ContentFile
from factory.django import DjangoModelFactory

from apps.certificates.models import Certificate
from apps.courses.tests.factories import EnrollmentFactory


class CertificateFactory(DjangoModelFactory):
    """Keep direct permission fixtures separate from issuance eligibility."""

    class Meta:
        """Bind certificates with synthetic PDF files."""

        model = Certificate

    enrollment = factory.SubFactory(EnrollmentFactory, status="COMPLETED")
    certificate_id = factory.Sequence(lambda n: f"CC-2026-{n + 1:05}")
    issued_on = date(2026, 11, 2)
    average_percent = Decimal("85.00")
    grade = "A"
    pdf = factory.LazyAttribute(
        lambda row: ContentFile(b"%PDF-1.4\n%%EOF\n", name="certificate.pdf")
    )
