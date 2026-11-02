"""Grow account, catalog and profile pages with real relevant child records."""

from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory, SubjectFactory
from apps.core.tests.query_pages import PageSetup
from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    QualificationFactory,
    TraineeProfileFactory,
    TrainerProfileFactory,
    WorkExperienceFactory,
)


def account_list(name: str) -> PageSetup:
    """Grow the actual admin list population while keeping its actor stable."""
    user = UserFactory(active_admin=True)
    UserFactory(pending_trainee=True)
    return PageSetup(
        reverse(name), user, lambda: UserFactory.create_batch(9, pending_trainee=True)
    )


def catalog_list() -> PageSetup:
    """Give every listed subject skills so all prefetch paths execute at both sizes."""
    user = UserFactory(approved_trainee=True)

    def add() -> None:
        """Add one populated subject rather than changing only unrelated table rows."""
        SkillFactory(subject=SubjectFactory())

    add()
    return PageSetup(
        reverse("catalog:subject_list"), user, lambda: [add() for _ in range(9)]
    )


def profile_directory() -> PageSetup:
    """Grow both eligible role populations in the shared directory."""
    user = UserFactory(approved_trainee=True)

    def add() -> None:
        """Exercise both profile lists with joined user display data."""
        TraineeProfileFactory()
        TrainerProfileFactory()

    add()
    return PageSetup(
        reverse("profiles:profile_list"), user, lambda: [add() for _ in range(9)]
    )


def _profile_children(profile: object) -> None:
    """Grow each displayed child type independently of file-serving routes."""
    QualificationFactory(profile=profile)
    WorkExperienceFactory(profile=profile)
    ExternalCertificateFactory(profile=profile)
    profile.skills.add(SkillFactory())


def trainee_detail() -> PageSetup:
    """Compare one versus ten qualifications, experiences, certificates and skills."""
    profile = TraineeProfileFactory()
    _profile_children(profile)
    return PageSetup(
        reverse("profiles:trainee_detail", args=[profile.pk]),
        profile.user,
        lambda: [_profile_children(profile) for _ in range(9)],
    )


def trainer_detail() -> PageSetup:
    """Keep the displayed trainer fixed while the profile population grows."""
    profile = TrainerProfileFactory()
    return PageSetup(
        reverse("profiles:trainer_detail", args=[profile.pk]),
        profile.user,
        lambda: TrainerProfileFactory.create_batch(9),
    )
