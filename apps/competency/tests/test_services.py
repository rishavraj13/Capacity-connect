"""Verify trainer ownership and real duplicate-insert collision handling."""

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.competency import services
from apps.competency.models import TrainerCompetency
from apps.competency.tests.factories import CompetencyFactory
from apps.core.exceptions import CapacityConnectError

pytestmark = pytest.mark.django_db
DATA = {"proficiency": 4, "years_experience": 7}


def test_declare_update_remove_and_retired_subject_preservation() -> None:
    """Allow existing retired declarations to remain editable without moving them."""
    user = UserFactory(approved_trainer=True)
    subject = SubjectFactory()
    row = services.declare_competency(user, subject, DATA)
    subject.is_active = False
    subject.save()
    assert services.update_competency(user, row, {"proficiency": 5}).proficiency == 5
    with pytest.raises(CapacityConnectError, match="cannot change"):
        services.update_competency(user, row, {"subject": SubjectFactory()})
    services.remove_competency(user, row)
    with pytest.raises(CapacityConnectError, match="active subject"):
        services.declare_competency(user, subject, DATA)


@pytest.mark.parametrize(
    "trait", ["approved_trainee", "active_admin", "pending_trainee", "rejected_user"]
)
def test_only_eligible_owner_can_declare_or_edit(trait: str) -> None:
    """Refuse Admin edits as well as cross-role and inactive service calls."""
    row = CompetencyFactory()
    user = UserFactory(**{trait: True})
    with pytest.raises(CapacityConnectError):
        services.declare_competency(user, row.subject, DATA)
    with pytest.raises(CapacityConnectError):
        services.update_competency(user, row, DATA)


def test_duplicate_and_insert_race_are_domain_errors() -> None:
    """Hit the real uniqueness constraint after validated input but before save."""
    row = CompetencyFactory()
    with pytest.raises(CapacityConnectError, match="already declared"):
        services.declare_competency(row.trainer, row.subject, DATA)
    trainer = UserFactory(approved_trainer=True)
    original = TrainerCompetency.save

    def competing(current: object, *args: object, **kwargs: object) -> None:
        """Insert the competing row inside the attempted savepoint."""
        if current.pk is None:
            original(TrainerCompetency(trainer=trainer, subject=row.subject, **DATA))
        return original(current, *args, **kwargs)

    with patch.object(TrainerCompetency, "save", competing):
        with pytest.raises(CapacityConnectError, match="Conflicting"):
            services.declare_competency(trainer, row.subject, DATA)


def test_other_trainer_idor_on_edit_and_remove(client: object) -> None:
    """Hide another trainer's declaration IDs before any mutable form access."""
    row = CompetencyFactory()
    user = UserFactory(approved_trainer=True)
    with pytest.raises(CapacityConnectError, match="owning"):
        services.update_competency(user, row, DATA)
    client.force_login(user)
    assert client.get(reverse("competency:edit", args=[row.pk])).status_code == 404
    assert client.post(reverse("competency:remove", args=[row.pk])).status_code == 404
