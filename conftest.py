"""Keep every test upload isolated from developer storage."""

import pytest


@pytest.fixture(autouse=True)
def temporary_upload_storage(settings: object, tmp_path: object) -> None:
    """Prevent test uploads from leaving files in the working project."""
    settings.MEDIA_ROOT = tmp_path / "public"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"
