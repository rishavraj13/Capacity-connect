"""Prove every profile form excludes privileged and ownership fields."""

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory
from apps.profiles.forms import (
    AccountForm,
    ExternalCertificateForm,
    QualificationForm,
    TraineeProfileForm,
    TrainerProfileForm,
    WorkExperienceForm,
)
from apps.profiles.tests.factories import TraineeProfileFactory


@pytest.mark.parametrize(
    "form_class",
    [
        AccountForm,
        TraineeProfileForm,
        TrainerProfileForm,
        QualificationForm,
        WorkExperienceForm,
        ExternalCertificateForm,
    ],
)
def test_forms_have_no_privileged_fields(form_class: type) -> None:
    """Make form mass-assignment surfaces explicit and auditable."""
    assert not {
        "user",
        "owner",
        "profile",
        "is_staff",
        "is_superuser",
        "is_approved",
        "is_active",
        "password",
    } & set(form_class.base_fields)
    if form_class is not WorkExperienceForm:
        assert "role" not in form_class.base_fields


@pytest.mark.django_db
def test_account_email_validation() -> None:
    """Normalize email and reject other owners' case variants."""
    user = UserFactory(approved_trainee=True)
    other = UserFactory()
    data = {"email": other.email.upper(), "first_name": "A", "last_name": "B"}
    assert not AccountForm(data, instance=user).is_valid()
    data["email"] = " NEW@Example.COM "
    form = AccountForm(data, instance=user)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["email"] == "new@example.com"


@pytest.mark.django_db
def test_trainee_form_rejects_inactive_skills() -> None:
    """Reject forged skill choices even when the browser omits selection controls."""
    profile = TraineeProfileFactory()
    skill = SkillFactory(subject__is_active=False)
    form = TraineeProfileForm({"skills": [skill.pk]}, instance=profile)
    assert not form.is_valid()


@pytest.mark.django_db
def test_work_experience_form_rejects_reversed_dates() -> None:
    """Report invalid date ranges before a child write is attempted."""
    form = WorkExperienceForm(
        {
            "organisation": "Company",
            "role": "Analyst",
            "start_date": "2022-01-01",
            "end_date": "2021-01-01",
        }
    )
    assert not form.is_valid()
    assert form.non_field_errors()
