"""Build role-correct learning workflow fixtures with deterministic dates."""

from datetime import date

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.courses.models import Course, Enrollment, Module, ModuleProgress


class CourseFactory(DjangoModelFactory):
    """Keep course ownership eligible unless a test explicitly changes it."""

    class Meta:
        """Bind fixtures to course records."""

        model = Course

    title = factory.Sequence(lambda n: f"Course {n}")
    subject = factory.SubFactory(SubjectFactory)
    trainer = factory.SubFactory(UserFactory, approved_trainer=True)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 12, 31)


class ModuleFactory(DjangoModelFactory):
    """Supply unique positive station orders by default."""

    class Meta:
        """Bind fixtures to course modules."""

        model = Module

    course = factory.SubFactory(CourseFactory)
    title = factory.Sequence(lambda n: f"Module {n}")
    order = factory.Sequence(lambda n: n + 1)


class EnrollmentFactory(DjangoModelFactory):
    """Keep trainee ownership and publication valid for service tests."""

    class Meta:
        """Bind fixtures to participation records."""

        model = Enrollment

    trainee = factory.SubFactory(UserFactory, approved_trainee=True)
    course = factory.SubFactory(CourseFactory, is_published=True)


class ModuleProgressFactory(DjangoModelFactory):
    """Place default progress on a module belonging to the enrollment's course."""

    class Meta:
        """Bind fixtures to station progress."""

        model = ModuleProgress

    enrollment = factory.SubFactory(EnrollmentFactory)
    module = factory.SubFactory(
        ModuleFactory, course=factory.SelfAttribute("..enrollment.course")
    )
    completed_at = factory.LazyFunction(timezone.now)
