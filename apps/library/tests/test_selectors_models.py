"""Verify private visibility, filters, query bounds and protected associations."""

import pytest
from django.db.models.deletion import ProtectedError

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory
from apps.library import selectors
from apps.library.constants import ResourceKind
from apps.library.tests.factories import ResourceFactory, resource_upload

pytestmark = pytest.mark.django_db


def test_resource_foreign_keys_are_protected() -> None:
    """Keep course, subject and trainer records referenced by evidence intact."""
    course = CourseFactory()
    resource = ResourceFactory(
        course=course, trainer=course.trainer, subject=course.subject
    )
    for target in (resource.trainer, resource.subject, resource.course):
        with pytest.raises(ProtectedError):
            target.delete()


def test_visibility_filtering_and_query_count(
    django_assert_num_queries: object,
) -> None:
    """Read list metadata in one query without leaking private owner drafts."""
    private = ResourceFactory()
    public = ResourceFactory(
        is_published=True, kind=ResourceKind.VIDEO, file=resource_upload("mp4")
    )
    trainee = UserFactory(approved_trainee=True)
    admin = UserFactory(active_admin=True)
    assert private in selectors.visible_resources(private.trainer)
    assert private in selectors.visible_resources(admin)
    assert private not in selectors.visible_resources(trainee)
    assert not selectors.managed_resources(trainee).exists()
    assert not selectors.visible_resources(UserFactory(pending_trainee=True)).exists()
    with django_assert_num_queries(1):
        resources = list(
            selectors.visible_resources(trainee, public.subject, ResourceKind.VIDEO)
        )
        assert [(item.trainer.username, item.subject.name) for item in resources] == [
            (public.trainer.username, public.subject.name)
        ]
