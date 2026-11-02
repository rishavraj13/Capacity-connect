"""Prove profile constraints survive direct writes and validation calls."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.profiles.constants import QUALIFICATION_YEAR_MAX, QUALIFICATION_YEAR_MIN
from apps.profiles.models import WorkExperience
from apps.profiles.tests.factories import (
    QualificationFactory,
    TraineeProfileFactory,
    TrainerProfileFactory,
    WorkExperienceFactory,
)

pytestmark = pytest.mark.django_db


def test_work_dates_database_constraint() -> None:
    """Allow ongoing work and reject reversed dates at the database boundary."""
    record = WorkExperienceFactory()
    assert record.end_date is None
    WorkExperience.objects.filter(pk=record.pk).update(end_date=record.start_date)
    with pytest.raises(IntegrityError), transaction.atomic():
        WorkExperience.objects.filter(pk=record.pk).update(end_date=date(2019, 1, 1))


@pytest.mark.parametrize("years", [-1, 61])
def test_trainer_years_validators(years: int) -> None:
    """Keep trainer claims within the authorized zero-to-sixty range."""
    profile = TrainerProfileFactory.build(years_experience=years)
    profile.user = TraineeProfileFactory().user
    with pytest.raises(ValidationError):
        profile.full_clean()


@pytest.mark.parametrize(
    "year", [QUALIFICATION_YEAR_MIN - 1, QUALIFICATION_YEAR_MAX + 1]
)
def test_qualification_year_bounds(year: int) -> None:
    """Apply named year bounds consistently in forms and services."""
    record = QualificationFactory.build(profile=TraineeProfileFactory(), year=year)
    with pytest.raises(ValidationError):
        record.full_clean()
