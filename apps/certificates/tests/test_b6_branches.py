"""Exercise real bounds, collisions and long text from the carry-over review."""

import re
from dataclasses import replace
from unittest.mock import patch

import pytest

from apps.certificates import services
from apps.certificates.exceptions import CertificateGenerationError
from apps.certificates.issuance import next_identifier
from apps.certificates.models import Certificate
from apps.certificates.pdf import render_certificate_pdf
from apps.certificates.tests.factories import CertificateFactory, certifiable_enrollment
from apps.certificates.tests.test_pdf import sample_data


@pytest.mark.django_db
def test_yearly_sequence_exhaustion_is_domain_error() -> None:
    """Prevent an overflowing public sequence after the last five-digit identifier."""
    CertificateFactory(certificate_id="CC-2026-99999")
    with pytest.raises(CertificateGenerationError, match="exhausted"):
        next_identifier(2026)


@pytest.mark.django_db
def test_issuance_unique_enrollment_race_returns_winner() -> None:
    """Exercise real one-to-one collision recovery after a competing row appears."""
    enrollment = certifiable_enrollment()
    original = services._insert

    def competing(current: object, average: object, issued: object) -> object:
        """Insert the winner before the real duplicate insert hits the constraint."""
        CertificateFactory(enrollment=current)
        return original(current, average, issued)

    with patch("apps.certificates.services._insert", side_effect=competing):
        row = services.issue_certificate(enrollment)
    assert Certificate.objects.count() == 1 and row.enrollment_id == enrollment.pk


def test_long_pdf_text_fits_and_uses_only_helvetica_times() -> None:
    """Exercise font shrinking and truncation without introducing fallback fonts."""
    payload = render_certificate_pdf(replace(sample_data(), trainee_name="A" * 1000))
    fonts = set(re.findall(rb"/BaseFont\s*/([^\s/<>\[\]()]+)", payload))
    assert fonts and fonts <= {
        b"Helvetica",
        b"Helvetica-Bold",
        b"Times-Roman",
        b"Times-Bold",
        b"Times-Italic",
    }
    assert b"Symbol" not in payload and payload.startswith(b"%PDF-")
