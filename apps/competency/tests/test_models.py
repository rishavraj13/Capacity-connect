"""Exercise direct database declaration uniqueness and both numeric ranges."""

import pytest
from django.db import IntegrityError, transaction

from apps.competency.tests.factories import CompetencyFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "values",
    [
        {"proficiency": 0},
        {"proficiency": 6},
        {"years_experience": -1},
        {"years_experience": 61},
    ],
)
def test_competency_database_bounds(values: dict) -> None:
    """Protect ranking inputs even if service validation is bypassed."""
    with pytest.raises(IntegrityError), transaction.atomic():
        CompetencyFactory(**values)


def test_competency_unique_trainer_subject() -> None:
    """Prevent duplicate ranking entries under direct concurrent inserts."""
    row = CompetencyFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        CompetencyFactory(trainer=row.trainer, subject=row.subject)
