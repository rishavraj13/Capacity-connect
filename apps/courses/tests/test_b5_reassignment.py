"""Keep derived questionnaire ownership synchronized with Admin reassignment."""

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import (
    AttemptFactory,
    QuestionFactory,
    QuestionnaireFactory,
)
from apps.core.exceptions import CapacityConnectError
from apps.courses.services import update_course
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


def test_reassignment_updates_all_questionnaires_atomically() -> None:
    """Allow a valid new trainer to own the course and every derived quiz."""
    question = QuestionFactory()
    quiz = question.questionnaire
    second = QuestionnaireFactory(course=quiz.course)
    AttemptFactory(questionnaire=second)
    new_trainer = UserFactory(approved_trainer=True)
    update_course(UserFactory(active_admin=True), quiz.course, {"trainer": new_trainer})
    quiz.refresh_from_db()
    second.refresh_from_db()
    assert quiz.trainer == second.trainer == new_trainer


def test_linked_resource_refuses_reassignment_with_relink_count() -> None:
    """Explain the independent library owner rather than silently rewriting it."""
    quiz = QuestionFactory().questionnaire
    ResourceFactory(course=quiz.course, trainer=quiz.trainer, subject=quiz.subject)
    with pytest.raises(
        CapacityConnectError, match="1 linked resource.*relink or unlink"
    ):
        update_course(
            UserFactory(active_admin=True),
            quiz.course,
            {"trainer": UserFactory(approved_trainer=True)},
        )
    quiz.refresh_from_db()
    quiz.course.refresh_from_db()
    assert quiz.course.trainer_id == quiz.trainer_id
