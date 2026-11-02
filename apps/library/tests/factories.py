"""Build private resource fixtures using the specified signature contracts."""

import factory
from django.core.files.uploadedfile import SimpleUploadedFile
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.library.constants import ResourceKind
from apps.library.models import LibraryResource

UPLOAD_BYTES = {
    "pdf": b"%PDF-1.7\n%%EOF",
    "mp4": b"\x00\x00\x00\x18ftypisom",
    "webm": b"\x1a\x45\xdf\xa3test",
    "pptx": b"PK\x03\x04presentation",
    "docx": b"PK\x03\x04document",
}


def resource_upload(extension: str = "pdf") -> SimpleUploadedFile:
    """Provide minimal bytes matching the deliberately shallow signature contract."""
    return SimpleUploadedFile(
        f"resource.{extension}", UPLOAD_BYTES[extension], content_type="text/html"
    )


class ResourceFactory(DjangoModelFactory):
    """Keep resources private and owner-isolated by default."""

    class Meta:
        """Bind fixtures to private resource metadata."""

        model = LibraryResource

    trainer = factory.SubFactory(UserFactory, approved_trainer=True)
    subject = factory.SubFactory(SubjectFactory)
    title = factory.Sequence(lambda n: f"Resource {n}")
    kind = ResourceKind.DOCUMENT
    file = factory.LazyFunction(resource_upload)
