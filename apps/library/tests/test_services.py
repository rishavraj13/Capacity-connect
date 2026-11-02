"""Verify private resource ownership, course associations and storage lifecycle."""

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.core.exceptions import CapacityConnectError
from apps.courses.tests.factories import CourseFactory
from apps.library import services
from apps.library.constants import ResourceKind
from apps.library.models import LibraryResource
from apps.library.tests.factories import ResourceFactory, resource_upload

pytestmark = pytest.mark.django_db


def resource_data(**changes: object) -> dict:
    """Supply valid defaults while preserving each test's focused rule change."""
    return {
        "title": "Reference",
        "description": "Details",
        "subject": SubjectFactory(),
        "course": None,
        "kind": ResourceKind.DOCUMENT,
        "file": resource_upload(),
        **changes,
    }


def test_resource_creation_publication_and_admin_assignment() -> None:
    """Keep owner and publication mass assignment on explicit service paths."""
    owner = UserFactory(approved_trainer=True)
    other = UserFactory(approved_trainer=True)
    resource = services.create_resource(
        owner, resource_data(trainer=other, is_published=True)
    )
    assert resource.trainer == owner and not resource.is_published
    assert str(resource) == resource.title
    assert services.publish(owner, resource).is_published
    assert not services.unpublish(owner, resource).is_published
    admin = UserFactory(active_admin=True)
    assigned = services.create_resource(admin, resource_data(trainer=other))
    assert assigned.trainer == other
    updated = services.update_resource(
        admin, assigned, {"title": "Updated", "trainer": owner}
    )
    assert updated.trainer == owner and updated.title == "Updated"


def test_optional_course_must_match_trainer_and_subject() -> None:
    """Reject misleading course links even when browser choices are bypassed."""
    course = CourseFactory()
    valid = services.create_resource(
        course.trainer, resource_data(course=course, subject=course.subject)
    )
    assert valid.course == course
    with pytest.raises(CapacityConnectError, match="match"):
        services.create_resource(course.trainer, resource_data(course=course))
    other = UserFactory(approved_trainer=True)
    with pytest.raises(CapacityConnectError, match="match"):
        services.create_resource(
            other, resource_data(course=course, subject=course.subject)
        )
    with pytest.raises(CapacityConnectError, match="match"):
        services.update_resource(course.trainer, valid, {"subject": SubjectFactory()})


def test_file_replace_and_delete_cleanup(
    django_capture_on_commit_callbacks: object,
) -> None:
    """Delete previous bytes only after replacement/deletion transactions commit."""
    resource = ResourceFactory()
    storage, old = resource.file.storage, resource.file.name
    with django_capture_on_commit_callbacks(execute=True):
        updated = services.update_resource(
            resource.trainer, resource, {"file": resource_upload()}
        )
    assert not storage.exists(old) and storage.exists(updated.file.name)
    current = updated.file.name
    with django_capture_on_commit_callbacks(execute=True):
        services.delete_resource(updated.trainer, updated)
    assert not storage.exists(current) and not LibraryResource.objects.exists()


def test_ownership_and_upload_failures_are_domain_errors() -> None:
    """Reject unauthorized resource writes and missing/invalid file inputs cleanly."""
    resource = ResourceFactory()
    other = UserFactory(approved_trainer=True)
    for action in (services.publish, services.unpublish, services.delete_resource):
        with pytest.raises(CapacityConnectError):
            action(other, resource)
    with pytest.raises(CapacityConnectError):
        services.update_resource(other, resource, {"title": "Stolen"})
    with pytest.raises(CapacityConnectError, match="required"):
        services.create_resource(resource.trainer, resource_data(file=None))
    with pytest.raises(CapacityConnectError):
        services.create_resource(
            resource.trainer, resource_data(kind=ResourceKind.VIDEO)
        )


def test_invalid_description_is_domain_validation_feedback() -> None:
    """Translate model validation into the common service error hierarchy."""
    resource = ResourceFactory()
    with pytest.raises(CapacityConnectError):
        services.update_resource(resource.trainer, resource, {"title": ""})
