"""Produce unique catalog fixtures without external dependencies."""

import factory
from factory.django import DjangoModelFactory

from apps.catalog.models import Skill, Subject


class SubjectFactory(DjangoModelFactory):
    """Keep independent subjects isolated between tests."""

    class Meta:
        """Bind generated rows to the catalog model."""

        model = Subject

    name = factory.Sequence(lambda n: f"Subject {n}")


class SkillFactory(DjangoModelFactory):
    """Create a valid owning subject for each independent skill."""

    class Meta:
        """Bind generated rows to skills."""

        model = Skill

    name = factory.Sequence(lambda n: f"Skill {n}")
    subject = factory.SubFactory(SubjectFactory)
