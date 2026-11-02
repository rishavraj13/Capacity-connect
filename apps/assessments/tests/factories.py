"""Build deterministic protected assessment fixtures and valid option sets."""

from datetime import UTC, datetime, timedelta
from typing import Any

import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.assessments.models import (
    Attempt,
    AttemptAnswer,
    Option,
    Question,
    Questionnaire,
)
from apps.core import clock
from apps.courses.tests.factories import CourseFactory, EnrollmentFactory

MOMENT = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


class QuestionnaireFactory(DjangoModelFactory):
    """Provide a draft with matching course ownership and subject."""

    class Meta:
        """Bind fixture data to quiz metadata."""

        model = Questionnaire

    course = factory.SubFactory(CourseFactory, is_published=True)
    subject = factory.SelfAttribute("course.subject")
    trainer = factory.SelfAttribute("course.trainer")
    title = factory.Sequence(lambda n: f"Assessment {n}")
    opens_at = MOMENT - timedelta(hours=1)
    deadline = MOMENT + timedelta(hours=1)
    duration_minutes = 5


class QuestionFactory(DjangoModelFactory):
    """Keep default questions ready with exactly two choices and one correct."""

    class Meta:
        """Bind fixture data to protected questions."""

        model = Question
        skip_postgeneration_save = True

    questionnaire = factory.SubFactory(QuestionnaireFactory)
    text = factory.Sequence(lambda n: f"Question {n}")
    order = factory.Sequence(lambda n: n + 1)
    marks = 1

    @factory.post_generation
    def options(self, create: bool, extracted: object, **kwargs: Any) -> None:
        """Create a valid minimal choice set without relying on service behavior."""
        if create:
            OptionFactory(question=self, text="Choice Alpha", is_correct=True)
            OptionFactory(question=self, text="Choice Beta", is_correct=False)


class OptionFactory(DjangoModelFactory):
    """Create extra or explicitly invalid choices only when a test requests them."""

    class Meta:
        """Bind fixture data to choices."""

        model = Option

    question = factory.SubFactory(QuestionFactory)
    text = factory.Sequence(lambda n: f"Option {n}")
    is_correct = False


class AttemptFactory(DjangoModelFactory):
    """Supply patchable start timestamps without automatically grading anything."""

    class Meta:
        """Bind fixture data to attempt history."""

        model = Attempt

    questionnaire = factory.SubFactory(QuestionnaireFactory)
    trainee = factory.SubFactory(UserFactory, approved_trainee=True)
    started_at = factory.LazyFunction(lambda: clock.now())


class AnswerFactory(DjangoModelFactory):
    """Allow explicit historical answer rows for protection and timeout tests."""

    class Meta:
        """Bind fixture data to submitted answers."""

        model = AttemptAnswer

    attempt = factory.SubFactory(AttemptFactory)
    question = factory.SubFactory(
        QuestionFactory, questionnaire=factory.SelfAttribute("..attempt.questionnaire")
    )
    selected_option = factory.LazyAttribute(lambda row: row.question.options.first())
    is_correct = True


def ready_quiz(**changes: Any) -> tuple:
    """Give service tests a ready quiz and an eligible active trainee."""
    quiz = QuestionnaireFactory(**changes)
    question = QuestionFactory(questionnaire=quiz)
    enrollment = EnrollmentFactory(course=quiz.course)
    return quiz, question, enrollment.trainee
