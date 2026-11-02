"""Prove public draft exclusion, stable board grouping and bounded SQL reads."""

from datetime import timedelta

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.announcements import selectors, services
from apps.announcements.constants import Category
from apps.announcements.tests.factories import AnnouncementFactory
from apps.assessments.tests.factories import MOMENT

pytestmark = pytest.mark.django_db


def test_drafts_and_unpublished_items_never_appear_on_public_home_or_board(
    client: object,
) -> None:
    """Exclude drafts and withdrawn content even for logged-in visitors."""
    draft = AnnouncementFactory(title="SECRET_DRAFT")
    visible = AnnouncementFactory(published=True, title="PUBLIC_VISIBLE")
    hidden = AnnouncementFactory(published=True, title="WITHDRAWN_SECRET")
    services.unpublish(hidden.created_by, hidden)
    for user in (None, UserFactory(approved_trainee=True), visible.created_by):
        if user:
            client.force_login(user)
        else:
            client.logout()
        response = client.get("/")
        assert response.status_code == 200 and b"PUBLIC_VISIBLE" in response.content
        assert (
            b"SECRET_DRAFT" not in response.content
            and b"WITHDRAWN_SECRET" not in response.content
        )
    ids = {item.id for items in selectors.board().values() for item in items}
    assert ids == {visible.pk} and draft.pk not in ids


def test_public_body_is_escaped_with_only_line_breaks(client: object) -> None:
    """Render manual text safely rather than accepting administrator HTML."""
    AnnouncementFactory(published=True, body="<script>alert(1)</script>\nSecond line")
    response = client.get("/")
    assert b"<script>" not in response.content and b"&lt;script&gt;" in response.content
    assert b"<br>Second line" in response.content
    assert (
        b"/login/" in response.content
        and b"/signup/" in response.content
        and b"/verify/" in response.content
    )


def test_board_limits_each_category_and_orders_stably() -> None:
    """Limit newest rows per category with deterministic publication ordering."""
    admin = UserFactory(active_admin=True)
    for category in Category.values:
        for i in range(7):
            AnnouncementFactory(
                created_by=admin,
                category=category,
                published=True,
                published_at=MOMENT + timedelta(minutes=i),
            )
    result = selectors.board(per_category=2)
    assert list(result) == Category.values and all(
        len(items) == 2 for items in result.values()
    )
    assert all(
        items[0].published_at > items[1].published_at for items in result.values()
    )
    assert all(items == () for items in selectors.board(0).values())


@pytest.mark.parametrize("size", [1, 12], ids=["small", "large"])
def test_board_constant_query_count(
    size: int, django_assert_num_queries: object
) -> None:
    """Bound published board reads at one query regardless of source row count."""
    AnnouncementFactory.create_batch(size, published=True)
    with django_assert_num_queries(1):
        result = selectors.board()
    assert len(result[Category.NOTICE]) == min(size, 5)


def test_manage_list_filters_are_admin_only() -> None:
    """Allow draft filtering only within the private Admin selector."""
    row = AnnouncementFactory()
    AnnouncementFactory(
        published=True, created_by=row.created_by, category=Category.DEADLINE
    )
    assert list(selectors.manage_list(row.created_by, Category.NOTICE, "draft")) == [
        row
    ]
    assert selectors.manage_list(row.created_by, status="published").count() == 1
    assert not selectors.manage_list(UserFactory(approved_trainer=True)).exists()
