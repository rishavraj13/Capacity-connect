"""Use real files to prove cleanup age/reference gates and explicit deletion."""

import json
import os
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command

from apps.assessments.tests.factories import MOMENT
from apps.certificates.tests.factories import CertificateFactory
from apps.core import clock
from apps.core.orphans import cleanup_orphans, referenced_files

pytestmark = pytest.mark.django_db


def aged(path: Path, hours: int) -> Path:
    """Set deterministic modification times without sleeps or clock assumptions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"demo file")
    stamp = (MOMENT - timedelta(hours=hours)).timestamp()
    os.utime(path, (stamp, stamp))
    return path


def test_cleanup_dry_run_delete_and_reference_age_guards(settings: object) -> None:
    """Keep old referenced files and recent orphans while removing only aged orphans."""
    referenced, orphan, public, recent = cleanup_fixture(settings)
    with clock.at(MOMENT):
        dry = StringIO()
        call_command("cleanup_orphan_files", stdout=dry)
        assert (
            orphan.exists()
            and public.exists()
            and "deleted=0 dry_run=True" in dry.getvalue()
        )
        deleted = StringIO()
        call_command("cleanup_orphan_files", delete=True, stdout=deleted)
    assert (
        not orphan.exists()
        and not public.exists()
        and recent.exists()
        and referenced.exists()
    )
    assert "orphans=2 deleted=2 dry_run=False" in deleted.getvalue()
    record_cleanup(dry, deleted, (referenced, recent))


def test_cleanup_rechecks_references_created_after_scan(settings: object) -> None:
    """Protect a real model reference that appears between scan and deletion."""
    path = aged(Path(settings.PRIVATE_MEDIA_ROOT) / "race.pdf", 30)
    original = referenced_files
    calls = 0

    def concurrent_reference() -> set:
        """Create a real FileField reference immediately before the deletion recheck."""
        nonlocal calls
        calls += 1
        if calls == 2:
            CertificateFactory(pdf="race.pdf")
        return original()

    with (
        clock.at(MOMENT),
        patch("apps.core.orphans.referenced_files", side_effect=concurrent_reference),
    ):
        result = cleanup_orphans(delete=True)
    assert result.candidates == (path,) and result.deleted == () and path.exists()


def test_cleanup_rejects_negative_age_and_handles_empty_roots(settings: object) -> None:
    """Refuse nonsensical ages and deduplicate coincident configured roots."""
    with pytest.raises(CommandError):
        call_command("cleanup_orphan_files", min_age_hours=-1, stdout=StringIO())
    settings.MEDIA_ROOT = settings.PRIVATE_MEDIA_ROOT
    with clock.at(MOMENT):
        assert cleanup_orphans().candidates == ()


def cleanup_fixture(settings: object) -> tuple:
    """Create real old referenced/orphan files and one recent orphan."""
    row = CertificateFactory()
    referenced = Path(row.pdf.path)
    stamp = (MOMENT - timedelta(hours=30)).timestamp()
    os.utime(referenced, (stamp, stamp))
    orphan = aged(Path(settings.PRIVATE_MEDIA_ROOT) / "orphan.pdf", 30)
    public = aged(Path(settings.MEDIA_ROOT) / "orphan.png", 30)
    recent = aged(Path(settings.PRIVATE_MEDIA_ROOT) / "recent.pdf", 1)
    return referenced, orphan, public, recent


def record_cleanup(dry: object, deleted: object, paths: tuple) -> None:
    """Keep command output and preservation proof in ignored local evidence."""
    referenced, recent = paths
    Path(".local/reports/B7_CLEANUP_PROOF.json").write_text(
        json.dumps(
            {
                "dry_run": dry.getvalue(),
                "delete": deleted.getvalue(),
                "referenced_preserved": referenced.exists(),
                "recent_preserved": recent.exists(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
