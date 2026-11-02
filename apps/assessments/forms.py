"""Validate grouped authoring input and correctness-free trainee selections."""

from typing import Any

from django import forms

from apps.assessments.authoring import validate_question_input
from apps.assessments.constants import (
    DEFAULT_PASS_PERCENT,
    MAX_ATTEMPTS,
    MAX_DURATION_MINUTES,
    MAX_OPTIONS,
    MAX_PASS_PERCENT,
    MIN_ATTEMPTS,
    MIN_DURATION_MINUTES,
    MIN_MARKS,
    MIN_PASS_PERCENT,
)
from apps.assessments.dataclasses import PaperQuestion, QuestionInput
from apps.assessments.exceptions import AssessmentRuleError
from apps.assessments.models import Question, Questionnaire

QUESTION_FIELD_PREFIX = "question_"
OPTION_NUMBER_BASE = 1


class QuestionnaireForm(forms.ModelForm):
    """Leave parent course, subject and trainer ownership to the service."""

    duration_minutes = forms.IntegerField(
        min_value=MIN_DURATION_MINUTES, max_value=MAX_DURATION_MINUTES
    )
    pass_percent = forms.IntegerField(
        min_value=MIN_PASS_PERCENT,
        max_value=MAX_PASS_PERCENT,
        initial=DEFAULT_PASS_PERCENT,
    )
    max_attempts = forms.IntegerField(
        min_value=MIN_ATTEMPTS, max_value=MAX_ATTEMPTS, initial=MIN_ATTEMPTS
    )

    class Meta:
        """Expose only author-editable descriptive and timing fields."""

        model = Questionnaire
        fields = (
            "title",
            "opens_at",
            "deadline",
            "duration_minutes",
            "pass_percent",
            "max_attempts",
        )


def question_input(data: dict) -> QuestionInput:
    """Convert human option numbers into the grouped domain input."""
    return QuestionInput(
        data["text"],
        tuple(data["options"]),
        data["correct_option"] - OPTION_NUMBER_BASE,
        data["marks"],
    )


class QuestionForm(forms.ModelForm):
    """Edit a question and its complete choice set in one validated form."""

    options = forms.CharField(
        widget=forms.Textarea, help_text="One option per line; provide 2 to 6 options."
    )
    correct_option = forms.IntegerField(
        min_value=OPTION_NUMBER_BASE,
        max_value=MAX_OPTIONS,
        initial=OPTION_NUMBER_BASE,
        help_text="Number of the correct option, starting at 1.",
    )
    marks = forms.IntegerField(min_value=MIN_MARKS, initial=MIN_MARKS)

    class Meta:
        """Keep order and questionnaire outside posted ownership fields."""

        model = Question
        fields = ("text", "marks")

    def clean_options(self) -> tuple[str, ...]:
        """Normalize line-separated choices before validating their count."""
        return tuple(
            line.strip()
            for line in self.cleaned_data["options"].splitlines()
            if line.strip()
        )

    def clean(self) -> dict:
        """Reuse the service's exact single-correct-choice input contract."""
        data = super().clean()
        if all(
            field in data for field in ("text", "options", "correct_option", "marks")
        ):
            try:
                validate_question_input(question_input(data))
            except AssessmentRuleError as exc:
                raise forms.ValidationError(exc.message) from exc
        return data


class AnswerForm(forms.Form):
    """Build radio fields from safe paper dataclasses only."""

    def __init__(
        self, paper: tuple[PaperQuestion, ...], *args: Any, **kwargs: Any
    ) -> None:
        """Keep correctness-bearing ORM models out of the take-page form."""
        super().__init__(*args, **kwargs)
        for question in paper:
            self.fields[f"{QUESTION_FIELD_PREFIX}{question.question_id}"] = (
                forms.TypedChoiceField(
                    choices=[
                        (option.option_id, option.text) for option in question.options
                    ],
                    coerce=int,
                    empty_value=None,
                    required=False,
                    label=question.text,
                    widget=forms.RadioSelect,
                )
            )

    def clean(self) -> dict:
        """Reject foreign question keys instead of silently ignoring their payload."""
        data = super().clean()
        if any(
            key.startswith(QUESTION_FIELD_PREFIX) and key not in self.fields
            for key in self.data
        ):
            raise forms.ValidationError("A question is outside this paper.")
        return data

    def selections(self) -> dict[int, int]:
        """Pass only answered option IDs to database-derived grading."""
        return {
            int(name.removeprefix(QUESTION_FIELD_PREFIX)): value
            for name, value in self.cleaned_data.items()
            if value is not None
        }
