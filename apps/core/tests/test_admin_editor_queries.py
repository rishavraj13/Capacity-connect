"""Measure existing Admin landing and form reads at two sizes."""

from functools import partial

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.announcements.tests.factories import AnnouncementFactory
from apps.catalog.tests.factories import SkillFactory, SubjectFactory
from apps.core.tests.query_pages import PageSetup, assert_stable_page

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "route",
    (
        "admin_panel",
        "catalog:subject_create",
        "catalog:subject_edit",
        "catalog:skill_create",
        "catalog:skill_edit",
        "announcements:create",
        "announcements:edit",
    ),
)
def test_admin_editor_queries_are_constant(client: object, route: str) -> None:
    """Grow catalog choices and announcements without changing read costs."""
    admin = UserFactory(active_admin=True)
    skill = SkillFactory()
    row = AnnouncementFactory(created_by=admin)
    args = {
        "catalog:subject_edit": (skill.subject_id,),
        "catalog:skill_edit": (skill.pk,),
        "announcements:edit": (row.pk,),
    }.get(route, ())
    grow = (
        partial(AnnouncementFactory.create_batch, 9, created_by=admin)
        if route.startswith("announcements:")
        else partial(SubjectFactory.create_batch, 9)
    )
    setup = PageSetup(reverse(route, args=args), admin, grow)
    assert_stable_page(client, f"F4 {route}", setup)
