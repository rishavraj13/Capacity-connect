"""Build independent trainer declarations for ranking and boundary tests."""

import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.competency.models import TrainerCompetency


class CompetencyFactory(DjangoModelFactory):
    """Create eligible declarations without relying on service behavior."""

    class Meta:
        """Bind direct competency fixtures."""

        model = TrainerCompetency

    trainer = factory.SubFactory(UserFactory, approved_trainer=True)
    subject = factory.SubFactory(SubjectFactory)
    proficiency = 3
    years_experience = 5
