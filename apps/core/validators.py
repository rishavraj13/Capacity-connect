"""Validate actual upload bytes before private files enter storage."""

from pathlib import PurePath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, UnidentifiedImageError

IMAGE_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG"}
PDF_SIGNATURE = b"%PDF-"


def validate_extension(file: UploadedFile, allowed: tuple[str, ...]) -> str:
    """Refuse filenames that cannot represent an allowed document type."""
    extension = PurePath(file.name).suffix.lower().lstrip(".")
    if extension not in allowed:
        raise ValidationError("Unsupported file extension.")
    return extension


def validate_size(file: UploadedFile, limit: int) -> None:
    """Bound parser work and reject empty uploads before inspecting content."""
    if not file.size or file.size > limit:
        raise ValidationError("File is empty or exceeds the upload size limit.")


def validate_content(file: UploadedFile, extension: str) -> None:
    """Check the file format independently of browser supplied MIME headers."""
    position = file.tell()
    try:
        file.seek(0)
        if extension == "pdf":
            if file.read(len(PDF_SIGNATURE)) != PDF_SIGNATURE:
                raise ValidationError("Invalid PDF content.")
        else:
            image = Image.open(file)
            if image.format != IMAGE_FORMATS[extension]:
                raise ValidationError("Image content does not match its extension.")
            image.verify()
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
    ) as exc:
        raise ValidationError("Invalid image content.") from exc
    finally:
        file.seek(position)


def validate_photo(file: UploadedFile) -> None:
    """Apply the shared photo contract at model and form boundaries."""
    extension = validate_extension(file, settings.PHOTO_EXTENSIONS)
    validate_size(file, settings.PHOTO_MAX_BYTES)
    validate_content(file, extension)


def validate_certificate(file: UploadedFile) -> None:
    """Allow documents and images only after size and content verification."""
    extension = validate_extension(file, settings.CERTIFICATE_EXTENSIONS)
    validate_size(file, settings.CERTIFICATE_MAX_BYTES)
    validate_content(file, extension)
