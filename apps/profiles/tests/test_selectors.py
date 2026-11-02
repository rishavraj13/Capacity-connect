"""Prove visibility filtering and bounded profile query costs."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory
from apps.profiles import selectors
from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    QualificationFactory,
    TraineeProfileFactory,
    TrainerProfileFactory,
    WorkExperienceFactory,
)

pytestmark = pytest.mark.django_db


def test_visibility_is_filtered_before_object_lookup() -> None:
    """Keep trainee history private while publishing trainer profiles internally."""
    trainee = TraineeProfileFactory()
    trainer = TrainerProfileFactory()
    admin = UserFactory(active_admin=True)
    certificate = ExternalCertificateFactory(profile=trainee)
    assert trainee in selectors.visible_trainees(trainee.user)
    assert trainee in selectors.visible_trainees(admin)
    assert not selectors.visible_trainees(trainer.user).exists()
    assert trainer in selectors.visible_trainers(trainee.user)
    assert certificate in selectors.visible_certificates(admin)
    pending = UserFactory(pending_trainee=True)
    assert not selectors.visible_trainees(pending).exists()
    assert not selectors.visible_trainers(pending).exists()
    assert list(selectors.own_trainee(trainee.user)) == [trainee]
    assert list(selectors.own_trainer(trainer.user)) == [trainer]


@pytest.mark.parametrize(
    "child_count", [1, 10], ids=["one-child-each", "ten-children-each"]
)
def test_profile_page_query_count(
    client: Client, django_assert_num_queries: object, child_count: int
) -> None:
    """Keep all profile sections independent of child and skill counts."""
    profile = TraineeProfileFactory()
    profile.skills.set(SkillFactory.create_batch(3))
    QualificationFactory.create_batch(child_count, profile=profile)
    WorkExperienceFactory.create_batch(child_count, profile=profile)
    ExternalCertificateFactory.create_batch(child_count, profile=profile)
    client.force_login(profile.user)
    with django_assert_num_queries(8):
        response = client.get(reverse("profiles:trainee_detail", args=[profile.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_skill_choices_for_new_profile() -> None:
    """Restrict a new unsaved profile to active catalog options."""
    from apps.profiles.models import TraineeProfile

    active = SkillFactory()
    SkillFactory(subject__is_active=False)
    assert list(selectors.skill_choices(TraineeProfile())) == [active]


def test_existing_and_active_choices_do_not_duplicate_shared_skills() -> None:
    """Keep a shared active skill unique when retained choices join owner history."""
    active = SkillFactory()
    owner = TraineeProfileFactory()
    other = TraineeProfileFactory()
    owner.skills.add(active)
    other.skills.add(active)
    assert list(selectors.skill_choices(owner)) == [active]
