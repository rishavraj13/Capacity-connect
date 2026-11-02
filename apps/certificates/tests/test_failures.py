"""Verify generation failures clean their own storage writes and database rows."""

from pathlib import Path
from unittest.mock import patch

import pytest

from apps.certificates.exceptions import CertificateGenerationError
from apps.certificates.models import Certificate
from apps.certificates.services import issue_certificate
from apps.certificates.tests.factories import certifiable_enrollment

pytestmark = pytest.mark.django_db


def test_pdf_reference_save_failure_removes_new_file(settings: object) -> None:
    """Undo the just-created private file if persisting its reference fails."""
    enrollment = certifiable_enrollment()
    original = Certificate.save

    def fail_reference(row: Certificate, *args: object, **kwargs: object) -> None:
        """Fail only after the generated PDF reached storage."""
        if kwargs.get("update_fields") == ["pdf", "updated_at"]:
            raise OSError("storage metadata unavailable")
        return original(row, *args, **kwargs)

    with patch.object(Certificate, "save", fail_reference):
        with pytest.raises(CertificateGenerationError):
            issue_certificate(enrollment)
    assert not Certificate.objects.exists()
    assert not [p for p in Path(settings.PRIVATE_MEDIA_ROOT).rglob("*") if p.is_file()]


def test_cleanup_storage_failure_still_raises_generation_domain_error() -> None:
    """Keep a secondary cleanup I/O failure from escaping the completion savepoint."""
    from apps.core.storage import PrivateStorage

    enrollment = certifiable_enrollment()
    original = Certificate.save

    def fail_reference(row: Certificate, *args: object, **kwargs: object) -> None:
        """Reach cleanup after the file write by failing the reference update."""
        if kwargs.get("update_fields") == ["pdf", "updated_at"]:
            raise OSError("metadata write failed")
        return original(row, *args, **kwargs)

    with (
        patch.object(Certificate, "save", fail_reference),
        patch.object(PrivateStorage, "delete", side_effect=OSError("cleanup denied")),
    ):
        with pytest.raises(CertificateGenerationError):
            issue_certificate(enrollment)
    assert not Certificate.objects.exists()
