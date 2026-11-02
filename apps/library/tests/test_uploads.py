"""Verify kind-specific signatures, bounded sizes and opaque upload names."""

from pathlib import PurePosixPath
from uuid import UUID

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.uploads import UploadPath
from apps.core.validators import validate_signature
from apps.library.tests.factories import resource_upload
from apps.library.validation import validate_resource_upload

VALID_KINDS = [
    ("VIDEO", "mp4"),
    ("VIDEO", "webm"),
    ("PRESENTATION", "pptx"),
    ("PRESENTATION", "pdf"),
    ("DOCUMENT", "docx"),
    ("DOCUMENT", "pdf"),
]


@pytest.mark.parametrize("kind,extension", VALID_KINDS)
def test_valid_signatures_ignore_browser_mime(kind: str, extension: str) -> None:
    """Accept specified containers without trusting their text/html MIME header."""
    file = resource_upload(extension)
    validate_resource_upload(file, kind)
    assert file.tell() == 0


@pytest.mark.parametrize("kind,extension", VALID_KINDS)
def test_wrong_content_empty_and_oversize(
    kind: str, extension: str, settings: object
) -> None:
    """Reject fake containers, empty uploads and configurable size violations."""
    for data in (b"plain text", b""):
        with pytest.raises(ValidationError):
            validate_resource_upload(SimpleUploadedFile(f"bad.{extension}", data), kind)
    settings.LIBRARY_UPLOAD_LIMITS = {kind: 1}
    with pytest.raises(ValidationError):
        validate_resource_upload(resource_upload(extension), kind)


@pytest.mark.parametrize(
    "kind,extension", [("VIDEO", "pdf"), ("PRESENTATION", "docx"), ("DOCUMENT", "mp4")]
)
def test_wrong_extension_for_kind_is_rejected(kind: str, extension: str) -> None:
    """Keep an otherwise valid container from bypassing declared resource kind."""
    with pytest.raises(ValidationError):
        validate_resource_upload(resource_upload(extension), kind)


def test_invalid_kind_and_mp4_offset() -> None:
    """Require a known kind and ftyp at its specified byte offset."""
    with pytest.raises(ValidationError):
        validate_resource_upload(resource_upload(), "UNKNOWN")
    with pytest.raises(ValidationError):
        validate_resource_upload(SimpleUploadedFile("bad.mp4", b"ftypwrong"), "VIDEO")
    file = resource_upload("mp4")
    file.seek(1)
    validate_signature(file, "mp4")
    assert file.tell() == 1


def test_library_paths_remove_traversal_and_use_uuid(settings: object) -> None:
    """Discard client paths and retain only an allowlisted lower-case suffix."""
    naming = UploadPath("library_resources", settings.LIBRARY_EXTENSIONS)
    result = naming(None, r"..\..\outside.MP4")
    parts = PurePosixPath(result).parts
    assert parts[0] == "library_resources" and len(parts) == 2
    assert UUID(PurePosixPath(result).stem).version == 4
    assert result.endswith(".mp4")
