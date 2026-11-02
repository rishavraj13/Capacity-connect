"""Compose kind-specific extension, size and content validation for all writes."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from apps.core.validators import validate_extension, validate_signature, validate_size
from apps.library.constants import ResourceKind


def validate_resource_upload(file: UploadedFile, kind: str) -> None:
    """Enforce declared kind independently of browser MIME metadata."""
    if kind not in ResourceKind.values:
        raise ValidationError("Choose a valid resource kind.")
    extension = validate_extension(file, settings.LIBRARY_UPLOAD_EXTENSIONS[kind])
    validate_size(file, settings.LIBRARY_UPLOAD_LIMITS[kind])
    validate_signature(file, extension)
