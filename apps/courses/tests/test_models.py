"""Verify all course uniqueness/date/order constraints at the database boundary."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.courses.models import Course, Enrollment, Module, ModuleProgress
from apps.courses.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)

pytestmark = pytest.mark.django_db


def test_course_dates_constraint_and_protected_references() -> None:
    """Reject reversed dates and preserve referenced subjects/trainers."""
    course = CourseFactory()
    assert str(course) == course.title
    with pytest.raises(IntegrityError), transaction.atomic():
        Course.objects.filter(pk=course.pk).update(end_date=date(2025, 1, 1))
    for target in (course.subject, course.trainer):
        with pytest.raises(ProtectedError):
            target.delete()


def test_module_unique_order_and_positive_database_check() -> None:
    """Keep station identity and positive order safe without forms."""
    module = ModuleFactory(order=1)
    assert str(module) == module.title
    with pytest.raises(IntegrityError), transaction.atomic():
        Module.objects.create(course=module.course, title="Duplicate", order=1)
    with pytest.raises(IntegrityError), transaction.atomic():
        Module.objects.filter(pk=module.pk).update(order=0)


def test_enrollment_unique_and_protected_course_trainee() -> None:
    """Prevent duplicate enrollment and deletion of referenced history owners."""
    enrollment = EnrollmentFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        Enrollment.objects.create(trainee=enrollment.trainee, course=enrollment.course)
    for target in (enrollment.course, enrollment.trainee):
        with pytest.raises(ProtectedError):
            target.delete()


def test_progress_unique_protect_and_enrollment_cascade() -> None:
    """Retain progressed modules but remove progress with its enrollment."""
    progress = ModuleProgressFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        ModuleProgress.objects.create(
            enrollment=progress.enrollment,
            module=progress.module,
            completed_at=progress.completed_at,
        )
    with pytest.raises(ProtectedError):
        progress.module.delete()
    progress.enrollment.delete()
    assert not ModuleProgress.objects.exists()


def test_course_deletion_cascades_unreferenced_modules() -> None:
    """Give the schema its specified cascade without exposing a deletion service."""
    module = ModuleFactory()
    module.course.delete()
    assert not Module.objects.exists()
