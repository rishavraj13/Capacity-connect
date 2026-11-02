"""Verify private downloads, safe filtering and unpublished object denial."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.library.constants import LIBRARY_PAGE_SIZE, ResourceKind
from apps.library.tests.factories import ResourceFactory, resource_upload

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "case",
    [
        (ResourceKind.VIDEO, "mp4", "inline;", "video/mp4"),
        (ResourceKind.VIDEO, "webm", "inline;", "video/webm"),
        (
            ResourceKind.PRESENTATION,
            "pptx",
            "attachment;",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
        (
            ResourceKind.DOCUMENT,
            "docx",
            "attachment;",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        (ResourceKind.DOCUMENT, "pdf", "attachment;", "application/pdf"),
    ],
    ids=["mp4", "webm", "pptx", "docx", "pdf"],
)
def test_download_headers(client: Client, case: tuple) -> None:
    """Select delivery headers from validated extension and kind, never upload MIME."""
    kind, extension, disposition, content_type = case
    resource = ResourceFactory(
        is_published=True, kind=kind, file=resource_upload(extension)
    )
    client.force_login(UserFactory(approved_trainee=True))
    response = client.get(reverse("library:download", args=[resource.pk]))
    assert response["Content-Type"] == content_type
    assert response["Content-Disposition"].startswith(disposition)
    assert response["Cache-Control"] == "private, no-store"
    assert b"".join(response.streaming_content)


def test_video_range_is_currently_full_response(client: Client) -> None:
    """Record the deployment Range limitation without pretending videos can seek."""
    resource = ResourceFactory(
        is_published=True, kind=ResourceKind.VIDEO, file=resource_upload("mp4")
    )
    client.force_login(UserFactory(approved_trainee=True))
    response = client.get(
        reverse("library:download", args=[resource.pk]), HTTP_RANGE="bytes=0-3"
    )
    assert response.status_code == 200 and "Content-Range" not in response
    response.close()


def test_unpublished_resources_hidden_from_other_users(client: Client) -> None:
    """Return object-level 404 for private metadata and file bytes."""
    resource = ResourceFactory()
    client.force_login(UserFactory(approved_trainer=True))
    for name in ("detail", "download", "edit"):
        assert (
            client.get(reverse(f"library:{name}", args=[resource.pk])).status_code
            == 404
        )
    for name in ("delete", "publish", "unpublish"):
        assert (
            client.post(reverse(f"library:{name}", args=[resource.pk])).status_code
            == 404
        )


def test_pagination_and_invalid_filter_are_safe(client: Client) -> None:
    """Keep lists at twenty rows and avoid invalid-ID lookup failures."""
    ResourceFactory.create_batch(21, is_published=True)
    client.force_login(UserFactory(approved_trainee=True))
    first = client.get(reverse("library:list"))
    assert len(first.context["page_obj"]) == LIBRARY_PAGE_SIZE
    second = client.get(reverse("library:list"), {"page": 2})
    assert len(second.context["page_obj"]) == 1
    invalid = client.get(reverse("library:list"), {"subject": "not-an-id"})
    assert invalid.status_code == 200 and not list(invalid.context["page_obj"])


def test_missing_private_file_is_404(client: Client) -> None:
    """Hide missing storage objects without leaking an internal server error."""
    resource = ResourceFactory()
    resource.file.storage.delete(resource.file.name)
    client.force_login(resource.trainer)
    assert (
        client.get(reverse("library:download", args=[resource.pk])).status_code == 404
    )


def test_public_resource_does_not_expose_unpublished_course_metadata(
    client: Client,
) -> None:
    """Keep a published file from bypassing its linked course's visibility policy."""
    from apps.courses.tests.factories import CourseFactory

    course = CourseFactory(title="Hidden course title")
    resource = ResourceFactory(
        is_published=True, course=course, trainer=course.trainer, subject=course.subject
    )
    client.force_login(UserFactory(approved_trainee=True))
    response = client.get(reverse("library:detail", args=[resource.pk]))
    assert response.status_code == 200
    assert course.title.encode() not in response.content


def test_resource_course_link_is_shown_when_visible(client: Client) -> None:
    """Keep navigation to a linked course for its enrolled trainee."""
    from apps.courses.tests.factories import CourseFactory, EnrollmentFactory

    course = CourseFactory(title="Enrolled private course")
    trainee = UserFactory(approved_trainee=True)
    EnrollmentFactory(course=course, trainee=trainee)
    resource = ResourceFactory(
        is_published=True, course=course, trainer=course.trainer, subject=course.subject
    )
    client.force_login(trainee)
    response = client.get(reverse("library:detail", args=[resource.pk]))
    assert course.title.encode() in response.content
