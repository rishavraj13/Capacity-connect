"""Verify Admin content workflows, safe state methods and CSRF on every mutation."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.announcements.models import Announcement
from apps.announcements.tests.factories import AnnouncementFactory
from apps.competency.tests.factories import CompetencyFactory

pytestmark = pytest.mark.django_db


def test_admin_announcement_form_create_edit_publish_and_manage(client: object) -> None:
    """Keep forged publication fields inert and drafts restricted to Admin."""
    user = UserFactory(active_admin=True)
    client.force_login(user)
    data = {
        "title": "Manual announcement",
        "body": "Body",
        "category": "NOTICE",
        "is_published": True,
        "created_by": 999,
    }
    assert client.post(reverse("announcements:create"), data).status_code == 302
    row = Announcement.objects.get()
    assert not row.is_published and row.created_by == user
    assert_edit_publish_flow(client, row, data)


@pytest.mark.parametrize(
    "name",
    [
        "announcements:create",
        "announcements:edit",
        "announcements:publish",
        "announcements:unpublish",
        "announcements:delete",
        "competency:add",
        "competency:edit",
        "competency:remove",
    ],
)
def test_csrf_on_all_new_mutation_routes(name: str) -> None:
    """Require tokens for content/publication/declaration changes regardless of role."""
    competency = name.startswith("competency:")
    user = UserFactory(
        **({"approved_trainer": True} if competency else {"active_admin": True})
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    args = []
    if name not in {"announcements:create", "competency:add"}:
        row = (
            CompetencyFactory(trainer=user)
            if competency
            else AnnouncementFactory(created_by=user)
        )
        args = [row.pk]
    assert client.post(reverse(name, args=args), {}).status_code == 403


def test_non_admin_cannot_reach_any_draft_listing(client: object) -> None:
    """Keep unpublished data absent from every public or non-Admin list surface."""
    AnnouncementFactory(title="PRIVATE_DRAFT")
    for user in (
        UserFactory(approved_trainee=True),
        UserFactory(approved_trainer=True),
    ):
        client.force_login(user)
        assert client.get(reverse("announcements:manage")).status_code == 403
        assert b"PRIVATE_DRAFT" not in client.get("/").content


def assert_edit_publish_flow(client: object, row: object, data: dict) -> None:
    """Keep edit and publication assertions together after draft creation."""
    assert (
        client.post(
            reverse("announcements:edit", args=[row.pk]),
            dict(data, title="Edited title"),
        ).status_code
        == 302
    )
    assert b"Edited title" in client.get(reverse("announcements:manage")).content
    assert (
        client.post(reverse("announcements:publish", args=[row.pk])).status_code == 302
    )
    assert b"Edited title" in client.get("/").content
    assert (
        client.post(reverse("announcements:unpublish", args=[row.pk])).status_code
        == 302
    )
    assert b"Edited title" not in client.get("/").content


def test_admin_manage_paginates_twenty_rows(client: object) -> None:
    """Keep draft-inclusive management lists bounded at twenty rows."""
    user = UserFactory(active_admin=True)
    AnnouncementFactory.create_batch(21, created_by=user)
    client.force_login(user)
    url = reverse("announcements:manage")
    assert len(client.get(url).context["page"]) == 20
    assert len(client.get(url, {"page": 2}).context["page"]) == 1
