"""Expose descriptive course input without trusting browser ownership flags."""

from typing import Any

from django import forms

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.selectors import approved_users
from apps.catalog.selectors import all_skills, all_subjects
from apps.courses.models import Course, Module


class CourseForm(forms.ModelForm):
    """Let only Admin explicitly select course trainer ownership."""

    class Meta:
        """Keep publication outside editable form fields."""

        model = Course
        fields = (
            "title",
            "description",
            "subject",
            "trainer",
            "start_date",
            "end_date",
        )

    def __init__(self, *args: Any, actor: User, **kwargs: Any) -> None:
        """Limit trainer choices using the current server-side actor."""
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = all_subjects()
        self.fields["trainer"].queryset = approved_users(UserRole.TRAINER)
        if actor.role != UserRole.ADMIN:
            self.fields.pop("trainer")


class ModuleForm(forms.ModelForm):
    """Permit cross-subject skills for interchange stations without owner input."""

    class Meta:
        """Leave course assignment to the service."""

        model = Module
        fields = ("title", "order", "skills")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Resolve catalog choices through the read boundary."""
        super().__init__(*args, **kwargs)
        self.fields["skills"].queryset = all_skills()
