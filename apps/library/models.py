"""Store resource metadata separately from protected private bytes."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.storage import PrivateStorage
from apps.core.uploads import UploadPath
from apps.library.constants import TITLE_MAX_LENGTH, ResourceKind


class LibraryResource(TimeStampedModel):
    """Preserve trainer, subject and optional course references deliberately."""

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="library_resources",
    )
    subject = models.ForeignKey(
        "catalog.Subject", on_delete=models.PROTECT, related_name="library_resources"
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.PROTECT,
        related_name="library_resources",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    kind = models.CharField(
        max_length=max(map(len, ResourceKind.values)), choices=ResourceKind.choices
    )
    file = models.FileField(
        storage=PrivateStorage(),
        upload_to=UploadPath("library_resources", settings.LIBRARY_EXTENSIONS),
    )
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        """Keep resource pagination deterministic."""

        ordering = ("pk",)

    def __str__(self) -> str:
        """Give resource choices a readable label."""
        return self.title
