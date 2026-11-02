"""Prevent private files from acquiring public media URLs."""

from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateStorage(FileSystemStorage):
    """Require callers to use the permission-checked download route."""

    @property
    def base_location(self) -> str:
        """Use private storage configuration instead of the public media root."""
        return str(self._value_or_setting(self._location, settings.PRIVATE_MEDIA_ROOT))

    @property
    def location(self) -> str:
        """Honor runtime settings overrides without cached public-root locations."""
        return str(Path(self.base_location).resolve())

    def url(self, name: str) -> str:
        """Fail loudly if a template tries to bypass file authorization."""
        raise ValueError("Private files have no public URL.")
