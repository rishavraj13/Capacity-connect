"""Validate catalog input without exposing lifecycle flags."""

from django import forms

from apps.catalog.models import Skill, Subject
from apps.catalog.selectors import subjects_for_skill


class SubjectForm(forms.ModelForm):
    """Expose only administrator-editable descriptive fields."""

    class Meta:
        """Keep activation state on explicit POST actions."""

        model = Subject
        fields = ("name", "description")


class SkillForm(forms.ModelForm):
    """Reject inactive subject choices before reaching the service."""

    class Meta:
        """Restrict mass assignment to catalog details."""

        model = Skill
        fields = ("name", "subject")

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Include an existing retired subject only for an unchanged assignment."""
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = subjects_for_skill(self.instance)
