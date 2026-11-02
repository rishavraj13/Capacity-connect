"""Prevent private files from acquiring public media URLs."""

from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateStorage(FileSystemStorage):
    """Require callers to use the permission-checked download route."""

    def url(self, name: str) -> str:
        """Fail loudly if a template tries to bypass file authorization."""
        raise ValueError("Private files have no public URL.")
