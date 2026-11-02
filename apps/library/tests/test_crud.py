"""Exercise resource forms, service validation and commit-time file cleanup."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory
from apps.library.models import LibraryResource
from apps.library.tests.factories import ResourceFactory, resource_upload

pytestmark = pytest.mark.django_db


def resource_form_data(course: object) -> dict:
    """Keep resource association input valid for the owning trainer."""
    return {
        "title": "HTTP resource",
        "description": "Details",
        "kind": "DOCUMENT",
        "subject": course.subject_id,
        "course": course.pk,
    }


def test_create_form_sets_owner_and_rejects_mass_assignment(client: Client) -> None:
    """Keep submitted trainer/publication/privilege flags out of trainer writes."""
    course = CourseFactory()
    client.force_login(course.trainer)
    data = dict(
        resource_form_data(course),
        file=resource_upload(),
        trainer=UserFactory(approved_trainer=True).pk,
        is_published=True,
        role="ADMIN",
    )
    assert client.post(reverse("library:create"), data).status_code == 302
    resource = LibraryResource.objects.get(title="HTTP resource")
    assert resource.trainer == course.trainer and not resource.is_published


def test_edit_replace_delete_forms_cleanup_files(
    client: Client, django_capture_on_commit_callbacks: object
) -> None:
    """Honor the private-file widget and clean up old evidence after commit."""
    course = CourseFactory()
    resource = ResourceFactory(
        course=course, subject=course.subject, trainer=course.trainer
    )
    old, storage = resource.file.name, resource.file.storage
    client.force_login(course.trainer)
    assert client.get(reverse("library:edit", args=[resource.pk])).status_code == 200
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("library:edit", args=[resource.pk]),
            dict(resource_form_data(course), file=resource_upload()),
        )
    assert response.status_code == 302 and not storage.exists(old)
    resource.refresh_from_db()
    current = resource.file.name
    with django_capture_on_commit_callbacks(execute=True):
        assert (
            client.post(reverse("library:delete", args=[resource.pk])).status_code
            == 302
        )
    assert not storage.exists(current)


def test_invalid_content_and_associations_render_form_errors(client: Client) -> None:
    """Reject bad bytes in forms and relationship mismatches in services."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.catalog.tests.factories import SubjectFactory

    course = CourseFactory()
    client.force_login(course.trainer)
    bad_file = dict(
        resource_form_data(course), file=SimpleUploadedFile("bad.pdf", b"plain text")
    )
    response = client.post(reverse("library:create"), bad_file)
    assert response.status_code == 200 and "file" in response.context["form"].errors
    mismatch = dict(
        resource_form_data(course), subject=SubjectFactory().pk, file=resource_upload()
    )
    response = client.post(reverse("library:create"), mismatch)
    assert response.status_code == 200 and response.context["form"].non_field_errors()
    assert not LibraryResource.objects.exists()
