"""Keep grades, certificate identifiers and PDF layout deterministic."""

from decimal import Decimal

from django.db import models


class Grade(models.TextChoices):
    """Label completed courses including below-fifty aggregate scores."""

    A = "A", "A"
    B = "B", "B"
    C = "C", "C"
    D = "D", "D"


GRADE_BANDS = (
    (Decimal("80"), Grade.A),
    (Decimal("65"), Grade.B),
    (Decimal("50"), Grade.C),
    (Decimal("0"), Grade.D),
)
ID_PREFIX = "CC"
ID_PATTERN = r"CC-[0-9]{4}-[0-9]{5}"
ID_RETRY_LIMIT = 5
MAX_SEQUENCE = 99999
PERCENT_QUANTUM = Decimal("0.01")
ZERO_PERCENT = Decimal("0.00")
MAX_PERCENT = Decimal("100.00")
PDF_FOLDER = "certificates"
PDF_EXTENSIONS = ("pdf",)
GOLD = "#b8892b"
INK = "#153248"
