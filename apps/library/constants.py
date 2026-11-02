"""Keep resource kinds and response media types explicit."""

from django.db.models import TextChoices

TITLE_MAX_LENGTH = 200
LIBRARY_PAGE_SIZE = 20


class ResourceKind(TextChoices):
    """Bind upload contracts and delivery behavior to a stable declared kind."""

    VIDEO = "VIDEO", "Video"
    PRESENTATION = "PRESENTATION", "Presentation"
    DOCUMENT = "DOCUMENT", "Document"


CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".pdf": "application/pdf",
    ".pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
