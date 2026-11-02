"""Name course states and bounds so workflows have one vocabulary."""

from django.db.models import TextChoices

TITLE_MAX_LENGTH = 200
FIRST_MODULE_ORDER = 1
INTERCHANGE_SUBJECT_COUNT = 2


class EnrollmentStatus(TextChoices):
    """Keep lifecycle values stable for later completion services."""

    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    DROPPED = "DROPPED", "Dropped"


class StationState(TextChoices):
    """Provide the frontend handoff states without presentation logic."""

    DONE = "DONE", "Done"
    CURRENT = "CURRENT", "Current"
    LOCKED = "LOCKED", "Locked"
