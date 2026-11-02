"""Build feedback independently of write-service eligibility."""

import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.courses.tests.factories import CourseFactory
from apps.feedback.models import Feedback


class FeedbackFactory(DjangoModelFactory):
    """Create retained course feedback for selectors and constraints."""

    class Meta:
        """Bind direct feedback fixtures."""

        model = Feedback

    author = factory.SubFactory(UserFactory, approved_trainee=True)
    course = factory.SubFactory(CourseFactory)
    rating = 4
    comment = "Helpful learning material."
