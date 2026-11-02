"""Validate resource input and filters without exposing publication flags."""

from typing import Any

from django import forms

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.selectors import approved_users
from apps.catalog.selectors import all_subjects
from apps.core.widgets import PrivateFileInput
from apps.courses.selectors import managed_courses
from apps.library.constants import ResourceKind
from apps.library.models import LibraryResource
from apps.library.validation import validate_resource_upload


class ResourceForm(forms.ModelForm):
    """Use the shared upload contract before a private file reaches services."""

    class Meta:
        """Keep publish state out of editable fields."""

        model = LibraryResource
        fields = (
            "title",
            "description",
            "trainer",
            "subject",
            "course",
            "kind",
            "file",
        )
        widgets = {"file": PrivateFileInput}

    def __init__(self, *args: Any, actor: User, **kwargs: Any) -> None:
        """Scope trainer-owned course choices without relying on posted ownership."""
        super().__init__(*args, **kwargs)
        self.fields["trainer"].queryset = approved_users(UserRole.TRAINER)
        self.fields["subject"].queryset = all_subjects()
        self.fields["course"].queryset = managed_courses(actor)
        if actor.role != UserRole.ADMIN:
            self.fields.pop("trainer")

    def clean(self) -> dict:
        """Reject kind/byte mismatches as file errors before service persistence."""
        data = super().clean()
        if data.get("file") and data.get("kind"):
            try:
                validate_resource_upload(data["file"], data["kind"])
            except forms.ValidationError as exc:
                self.add_error("file", exc)
        return data


class ResourceFilterForm(forms.Form):
    """Reject malformed filter IDs rather than sending them into ORM lookups."""

    subject = forms.ModelChoiceField(queryset=None, required=False)
    kind = forms.ChoiceField(
        choices=[("", "All kinds"), *ResourceKind.choices], required=False
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Keep filter choices fresh without import-time database queries."""
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = all_subjects()
