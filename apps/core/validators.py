"""Validate actual upload bytes before private files enter storage."""

import warnings
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


def _validate_image(file: UploadedFile, extension: str) -> None:
    """Treat Pillow's warning threshold as a rejection without global filters."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(file) as image:
            if image.format != IMAGE_FORMATS[extension]:
                raise ValidationError("Image content does not match its extension.")
            image.verify()


def validate_content(file: UploadedFile, extension: str) -> None:
    """Check the file format independently of browser supplied MIME headers."""
    position = file.tell()
    try:
        file.seek(0)
        if extension == "pdf":
            if file.read(len(PDF_SIGNATURE)) != PDF_SIGNATURE:
                raise ValidationError("Invalid PDF content.")
        else:
            _validate_image(file, extension)
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
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


CONTAINER_SIGNATURES = {
    "mp4": (4, b"ftyp"),
    "webm": (0, b"\x1a\x45\xdf\xa3"),
    "pptx": (0, b"PK\x03\x04"),
    "docx": (0, b"PK\x03\x04"),
    "pdf": (0, PDF_SIGNATURE),
}


def validate_signature(file: UploadedFile, extension: str) -> None:
    """Check container signatures without parsing office documents or videos."""
    offset, signature = CONTAINER_SIGNATURES[extension]
    position = file.tell()
    try:
        file.seek(offset)
        if file.read(len(signature)) != signature:
            raise ValidationError("File content does not match its extension.")
    finally:
        file.seek(position)
