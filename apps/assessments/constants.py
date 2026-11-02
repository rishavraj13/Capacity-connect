"""Name every assessment bound and persisted/public lifecycle value."""

from decimal import Decimal

from django.db.models import TextChoices

TITLE_MAX_LENGTH = 200
MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 240
MIN_PASS_PERCENT = 1
MAX_PASS_PERCENT = 100
DEFAULT_PASS_PERCENT = 50
MIN_ATTEMPTS = 1
MAX_ATTEMPTS = 10
FIRST_QUESTION_ORDER = 1
MIN_MARKS = 1
MIN_OPTIONS = 2
MAX_OPTIONS = 6
ATTEMPT_GRACE_SECONDS = 30
DEPARTURE_LIMIT = 5
PERCENT_SCALE = Decimal("100")
PERCENT_QUANTUM = Decimal("0.01")
ZERO_PERCENT = Decimal("0.00")


class AttemptStatus(TextChoices):
    """Distinguish submitted grading from rejected timed-out attempts."""

    IN_PROGRESS = "IN_PROGRESS", "In progress"
    SUBMITTED = "SUBMITTED", "Submitted"
    TIMED_OUT = "TIMED_OUT", "Timed out"


class DepartureStatus(TextChoices):
    """Expose only start-window state in the trainee departure handoff."""

    OPEN = "OPEN", "Open"
    UPCOMING = "UPCOMING", "Upcoming"
