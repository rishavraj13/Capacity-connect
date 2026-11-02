"""Keep public categories, text limits and pagination stable."""

from django.db import models


class Category(models.TextChoices):
    """Group manual posts in the departure-board handoff order."""

    NOTICE = "NOTICE", "Notice"
    ACHIEVEMENT = "ACHIEVEMENT", "Achievement"
    NEW_CONTENT = "NEW_CONTENT", "New content"
    DEADLINE = "DEADLINE", "Deadline"


TITLE_MAX_LENGTH = 200
BODY_MAX_LENGTH = 5000
PER_CATEGORY = 5
PAGE_SIZE = 20
STATUS_ALL = "all"
STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
