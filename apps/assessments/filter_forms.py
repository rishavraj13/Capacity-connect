"""Validate subject discovery against the trainee's enrolled assessment scope."""

from django import forms

from apps.assessments.usage_selectors import trainee_questionnaires
from apps.catalog.selectors import all_subjects


class AssessmentFilterForm(forms.Form):
    """Offer only enrolled assessment subjects without changing ownership rules."""

    subject = forms.ModelChoiceField(queryset=all_subjects().none(), required=False)

    def __init__(self, trainee: object, data: object = None) -> None:
        """Bind the choice catalogue to the same scoped questionnaire reader."""
        super().__init__(data)
        ids = trainee_questionnaires(trainee).values("subject_id")
        self.fields["subject"].queryset = (
            all_subjects().filter(pk__in=ids).order_by("name")
        )
