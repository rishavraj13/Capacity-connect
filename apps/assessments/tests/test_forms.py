"""Validate option count/correctness and keep ownership fields outside forms."""

import pytest

from apps.assessments.forms import QuestionForm, QuestionnaireForm


@pytest.mark.django_db
@pytest.mark.parametrize(
    "options,correct",
    [("A", 1), ("\n".join(str(n) for n in range(7)), 1), ("A\nB", 0), ("A\nB", 3)],
    ids=["too-few", "too-many", "no-correct", "outside-options"],
)
def test_question_form_requires_bounded_single_correct(
    options: str, correct: int
) -> None:
    """Reject both malformed choice counts and missing/out-of-range correct choices."""
    assert not QuestionForm(
        {"text": "Q", "marks": 1, "options": options, "correct_option": correct}
    ).is_valid()


def test_questionnaire_and_question_forms_have_no_owner_fields() -> None:
    """Prevent ownership, quota-state and privileged account mass assignment."""
    forbidden = {
        "course",
        "trainer",
        "subject",
        "questionnaire",
        "order",
        "status",
        "trainee",
        "role",
        "is_approved",
    }
    assert not forbidden & set(QuestionnaireForm.base_fields)
    assert not forbidden & set(QuestionForm.base_fields)
