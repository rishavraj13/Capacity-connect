"""Expose only role-appropriate details and validated private uploads."""

from django import forms

from apps.accounts.models import User
from apps.accounts.selectors import email_in_use
from apps.catalog.selectors import selectable_skills
from apps.core.widgets import PrivateFileInput
from apps.profiles.constants import (
    ACCOUNT_FIELDS,
    CERTIFICATE_FIELDS,
    EXPERIENCE_FIELDS,
    QUALIFICATION_FIELDS,
    TRAINEE_FIELDS,
    TRAINER_FIELDS,
)
from apps.profiles.models import (
    ExternalCertificate,
    Qualification,
    TraineeProfile,
    TrainerProfile,
    WorkExperience,
)


class TraineeProfileForm(forms.ModelForm):
    """Prevent profile owners from selecting retired catalog skills."""

    class Meta:
        """Exclude the owning user from posted fields."""

        model = TraineeProfile
        fields = (*TRAINEE_FIELDS, "skills")
        widgets = {"photo": PrivateFileInput}

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Rebuild available skills for each request's catalog state."""
        super().__init__(*args, **kwargs)
        self.fields["skills"].queryset = selectable_skills()


class TrainerProfileForm(forms.ModelForm):
    """Keep public trainer details independent of account privileges."""

    class Meta:
        """Allow only trainer presentation fields."""

        model = TrainerProfile
        fields = TRAINER_FIELDS
        widgets = {"photo": PrivateFileInput}


class QualificationForm(forms.ModelForm):
    """Prevent education records from being reassigned to another owner."""

    class Meta:
        """Let the service supply the owning profile."""

        model = Qualification
        fields = QUALIFICATION_FIELDS


class WorkExperienceForm(forms.ModelForm):
    """Validate dates before persisting employment history."""

    class Meta:
        """Keep ownership out of browser input."""

        model = WorkExperience
        fields = EXPERIENCE_FIELDS


class ExternalCertificateForm(forms.ModelForm):
    """Validate evidence files without exposing their storage paths."""

    class Meta:
        """Keep evidence ownership immutable through forms."""

        model = ExternalCertificate
        fields = CERTIFICATE_FIELDS
        widgets = {"file": PrivateFileInput}


class AccountForm(forms.ModelForm):
    """Allow every approved role to maintain basic contact details."""

    class Meta:
        """Exclude password, role, approval and staff flags."""

        model = User
        fields = ACCOUNT_FIELDS

    def clean_email(self) -> str:
        """Report case-insensitive email collisions before the database write."""
        email = self.cleaned_data["email"].strip().lower()
        if email_in_use(email, self.instance.pk):
            raise forms.ValidationError("A user with that email already exists.")
        return email
