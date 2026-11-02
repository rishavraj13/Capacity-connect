"""Build manual public/draft content with deterministic shared-clock timestamps."""

import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.announcements.constants import Category
from apps.announcements.models import Announcement
from apps.core import clock


class AnnouncementFactory(DjangoModelFactory):
    """Keep draft default and publication timestamps explicit in fixtures."""

    class Meta:
        """Bind direct announcement fixtures."""

        model = Announcement

    title = factory.Sequence(lambda n: f"Notice {n}")
    body = "Training information."
    category = Category.NOTICE
    is_published = False
    published_at = None
    created_by = factory.SubFactory(UserFactory, active_admin=True)

    class Params:
        """Provide ready public fixtures without publishing through the service."""

        published = factory.Trait(
            is_published=True, published_at=factory.LazyFunction(lambda: clock.now())
        )
