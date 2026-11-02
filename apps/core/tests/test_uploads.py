"""Exercise hostile uploads independently from browser supplied metadata."""

from pathlib import PurePosixPath
from uuid import UUID

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.uploads import UploadPath
from apps.core.validators import validate_certificate, validate_photo
from apps.profiles.tests.factories import pdf_upload, photo_upload


@pytest.mark.parametrize(
    "name,content",
    [
        ("bad.exe", b"%PDF-"),
        ("bad.pdf", b"plain text"),
        ("bad.png", b"plain text"),
        ("empty.pdf", b""),
    ],
)
def test_bad_uploads_are_rejected(name: str, content: bytes) -> None:
    """Reject extension spoofing, content spoofing and empty evidence."""
    with pytest.raises(ValidationError):
        validate_certificate(SimpleUploadedFile(name, content))


def test_limits_and_content_are_composable(settings: object) -> None:
    """Apply separate size, extension and image verification rules."""
    settings.PHOTO_MAX_BYTES = 1
    with pytest.raises(ValidationError):
        validate_photo(photo_upload())
    settings.CERTIFICATE_MAX_BYTES = 1
    with pytest.raises(ValidationError):
        validate_certificate(pdf_upload())
    with pytest.raises(ValidationError):
        validate_photo(pdf_upload())


def test_actual_images_and_pdf_signatures_are_accepted() -> None:
    """Preserve stream positions while validating real upload content."""
    image = photo_upload()
    validate_photo(image)
    assert image.tell() == 0
    validate_certificate(image)
    validate_certificate(pdf_upload())
    image.name = "wrong.jpg"
    with pytest.raises(ValidationError):
        validate_photo(image)


def test_upload_paths_discard_traversal_and_use_uuid() -> None:
    """Keep both Windows and POSIX user paths out of storage keys."""
    path = UploadPath("trainee_photos", ("png",))
    first = path(None, "../../secret.png")
    second = path(None, r"..\..\secret.png")
    assert first != second
    assert PurePosixPath(first).parts[0] == "trainee_photos"
    assert len(PurePosixPath(first).parts) == 2
    assert UUID(PurePosixPath(first).stem).version == 4
    with pytest.raises(ValidationError):
        path(None, "malware.exe")


def test_real_jpeg_and_uppercase_extension_are_accepted() -> None:
    """Permit both supported image encodings while normalizing storage suffixes."""
    from io import BytesIO

    from PIL import Image

    stream = BytesIO()
    Image.new("RGB", (2, 2)).save(stream, format="JPEG")
    file = SimpleUploadedFile("PHOTO.JPG", stream.getvalue())
    validate_photo(file)
    assert UploadPath("trainer_photos", ("jpg",))(None, file.name).endswith(".jpg")
