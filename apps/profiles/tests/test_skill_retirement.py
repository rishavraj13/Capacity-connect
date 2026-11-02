"""Preserve skill history when catalog offerings are retired."""

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from apps.catalog.services import deactivate_subject
from apps.catalog.tests.factories import SkillFactory
from apps.profiles import services
from apps.profiles.forms import TraineeProfileForm
from apps.profiles.tests.factories import TraineeProfileFactory

pytestmark = pytest.mark.django_db


def test_retired_selections_remain_visible_and_survive_form_save(
    client: Client,
) -> None:
    """Avoid silent data loss when a browser submits only current active choices."""
    profile = TraineeProfileFactory()
    selected = SkillFactory()
    profile.skills.add(selected)
    deactivate_subject(selected.subject)
    assert list(profile.skills.all()) == [selected]
    form = TraineeProfileForm(instance=profile)
    assert selected in form.fields["skills"].queryset
    client.force_login(profile.user)
    response = client.post(reverse("profiles:trainee_edit"), {"bio": "Updated"})
    assert response.status_code == 302
    assert list(profile.skills.all()) == [selected]


def test_service_retains_retired_skills_and_rejects_new_inactive_choices() -> None:
    """Enforce the same retirement contract outside the HTTP form path."""
    profile = TraineeProfileFactory()
    selected = SkillFactory()
    profile.skills.add(selected)
    deactivate_subject(selected.subject)
    services.update_trainee_profile(profile, {"skills": []})
    assert list(profile.skills.all()) == [selected]
    unselected = SkillFactory(subject__is_active=False)
    with pytest.raises(ValidationError):
        services.update_trainee_profile(profile, {"skills": [unselected]})
