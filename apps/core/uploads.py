"""Generate migration-safe opaque storage names for private uploads."""

from pathlib import PurePath
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db.models import Model
from django.utils.deconstruct import deconstructible


@deconstructible
class UploadPath:
    """Keep user-controlled paths out of storage keys."""

    def __init__(self, folder: str, extensions: tuple[str, ...]) -> None:
        """Persist upload naming configuration in migrations."""
        self.folder = folder
        self.extensions = extensions

    def __call__(self, instance: Model, filename: str) -> str:
        """Retain only a validated extension under a fixed model folder."""
        extension = PurePath(filename.replace("\\", "/")).suffix.lower().lstrip(".")
        if extension not in self.extensions:
            raise ValidationError("Unsupported file extension.")
        return f"{self.folder}/{uuid4().hex}.{extension}"
