"""Prove manual publication timestamp, validation and Admin-only write rules."""

from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction

from apps.accounts.tests.factories import UserFactory
from apps.announcements import services
from apps.announcements.tests.factories import AnnouncementFactory
from apps.assessments.tests.factories import MOMENT
from apps.core import clock
from apps.core.exceptions import CapacityConnectError

pytestmark = pytest.mark.django_db


def test_publish_idempotent_unpublish_retains_and_republish_restamps(
    monkeypatch: object,
) -> None:
    """Only unpublished-to-published transitions obtain a fresh clock instant."""
    admin = UserFactory(active_admin=True)
    row = services.create(
        admin,
        {"title": "Notice", "body": "Body", "category": "NOTICE", "is_published": True},
    )
    assert not row.is_published and row.published_at is None
    row = services.publish(admin, row)
    snapshot = row.updated_at
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(hours=1))
    repeated = services.publish(admin, row)
    assert repeated.published_at == MOMENT and repeated.updated_at == snapshot
    hidden = services.unpublish(admin, row)
    assert hidden.published_at == MOMENT and not hidden.is_published
    assert services.publish(admin, hidden).published_at == MOMENT + timedelta(hours=1)
    assert services.update(admin, row, {"title": "Edited"}).title == "Edited"
    services.delete(admin, row)


def test_published_timestamp_constraint_and_text_limits() -> None:
    """Keep direct publication data valid and service text inputs bounded."""
    with pytest.raises(IntegrityError), transaction.atomic():
        AnnouncementFactory(is_published=True, published_at=None)
    admin = UserFactory(active_admin=True)
    for values in ({"title": "x" * 201}, {"body": "x" * 5001}, {"category": "INVALID"}):
        with pytest.raises(CapacityConnectError):
            services.create(
                admin, {"title": "T", "body": "B", "category": "NOTICE", **values}
            )


@pytest.mark.parametrize(
    "trait",
    ["approved_trainee", "approved_trainer", "pending_trainee", "rejected_user"],
)
def test_non_admin_cannot_publish_or_create(trait: str) -> None:
    """Enforce Admin rules independently of view decorators."""
    user = UserFactory(**{trait: True})
    with pytest.raises(CapacityConnectError):
        services.create(user, {"title": "T", "body": "B", "category": "NOTICE"})
    row = AnnouncementFactory()
    with pytest.raises(CapacityConnectError):
        services.publish(user, row)
