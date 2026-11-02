"""Check one-page reproducible certificate bytes and built-in-font fallbacks."""

from datetime import date
from decimal import Decimal

import pytest

from apps.certificates.dataclasses import CertificateData
from apps.certificates.pdf import render_certificate_pdf


def sample_data(name: str = "Ananya Sharma") -> CertificateData:
    """Provide realistic immutable inputs without touching the database."""
    return CertificateData(
        name,
        "Applied Digital Skills",
        "Dr. Kavita Rao",
        "R. Menon",
        "Programme Director",
        "CC-2026-00001",
        date(2026, 11, 2),
        Decimal("83.34"),
        "A",
        "https://capacity.example/verify/CC-2026-00001/",
    )


@pytest.mark.parametrize(
    "name",
    ["Ananya Sharma", "Zoë Martin", "अनन्या शर्मा", "<script>(Name)\\"],
    ids=["latin", "latin-extended", "devanagari", "escaped-text"],
)
def test_certificate_pdf_is_one_page_reproducible_and_safe(name: str) -> None:
    """Produce readable PDF structure even for unsupported names or delimiters."""
    data = sample_data(name)
    payload = render_certificate_pdf(data)
    assert payload.startswith(b"%PDF-") and payload.rstrip().endswith(b"%%EOF")
    assert payload.count(b"/Type /Page\n") == 1 and b"/Count 1" in payload
    for text in (
        b"CERTIFICATE OF COMPLETION",
        b"Applied Digital Skills",
        b"CC-2026-00001",
        b"83.34%",
        b"Grade A",
        data.verification_url.encode(),
    ):
        assert text in payload
    assert payload == render_certificate_pdf(data)
    if name == "Ananya Sharma":
        assert name.encode() in payload
