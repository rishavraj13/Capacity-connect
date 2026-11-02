"""Keep every test upload isolated from developer storage."""

import pytest


@pytest.fixture(autouse=True)
def temporary_upload_storage(settings: object, tmp_path: object) -> None:
    """Prevent test uploads from leaving files in the working project."""
    settings.MEDIA_ROOT = tmp_path / "public"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"


@pytest.fixture(autouse=True)
def isolated_throttle_cache() -> object:
    """Prevent one test's abuse counters from leaking into another test's requests."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
