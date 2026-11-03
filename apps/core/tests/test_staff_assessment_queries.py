"""Compare response costs for shared assessment editors and authoring pages."""

from functools import partial

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import QuestionFactory, QuestionnaireFactory
from apps.core.tests.page_assessments import staff_page
from apps.core.tests.query_pages import PageSetup, assert_stable_page

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", ("owner", "admin"))
@pytest.mark.parametrize("route", ("course_list", "manage_detail", "participation"))
def test_staff_authoring_query_counts_remain_constant(
    client: object, role: str, route: str
) -> None:
    """Scale real questions, quizzes or participants for both authorized roles."""
    setup = staff_page(f"assessments:{route}")
    actor = setup.user if role == "owner" else UserFactory(active_admin=True)
    assert_stable_page(
        client, f"{role} quiz {route}", PageSetup(setup.url, actor, setup.expand)
    )


@pytest.mark.parametrize("role", ("owner", "admin"))
@pytest.mark.parametrize("route", ("create", "edit", "question_add", "question_edit"))
def test_staff_assessment_editors_have_constant_queries(
    client: object, role: str, route: str
) -> None:
    """Grow quizzes or questions behind the existing form reads."""
    quiz = QuestionnaireFactory()
    question = QuestionFactory(questionnaire=quiz)
    pk = {"create": quiz.course_id, "question_edit": question.pk}.get(route, quiz.pk)
    actor = quiz.trainer if role == "owner" else UserFactory(active_admin=True)
    setup = PageSetup(
        reverse(f"assessments:{route}", args=[pk]),
        actor,
        partial(QuestionFactory.create_batch, 9, questionnaire=quiz),
    )
    assert_stable_page(client, f"{role} quiz {route}", setup)
