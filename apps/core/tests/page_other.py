"""Grow feedback, certificates, announcements, competencies and dashboard pages."""

from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.announcements.tests.factories import AnnouncementFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.competency.tests.factories import CompetencyFactory
from apps.competency.tests.test_ranking import rated
from apps.core.tests.query_pages import PageSetup
from apps.courses.tests.factories import CourseFactory
from apps.dashboards.tests.factories import analytics_dataset
from apps.dashboards.tests.test_selectors import query_sources
from apps.feedback.tests.factories import FeedbackFactory
from apps.library.tests.factories import ResourceFactory


def feedback_page(kind: str, admin: bool = False) -> PageSetup:
    """Render own opinions or staff target summaries with repeated comment rows."""
    user = (
        UserFactory(active_admin=True) if admin else UserFactory(approved_trainee=True)
    )
    if kind == "mine":
        FeedbackFactory(author=user)
        return PageSetup(
            reverse("feedback:mine"),
            user,
            lambda: FeedbackFactory.create_batch(9, author=user),
        )
    target = CourseFactory() if kind == "course" else ResourceFactory()
    field = {kind: target}
    if kind == "resource":
        field["course"] = None
    FeedbackFactory(**field)
    actor = user if admin else target.trainer
    return PageSetup(
        reverse(f"feedback:{kind}_summary", args=[target.pk]),
        actor,
        lambda: FeedbackFactory.create_batch(9, **field),
    )


def certificate_page(verify: bool = False) -> PageSetup:
    """Grow private certificate history or public verification's related population."""
    row = CertificateFactory()
    url = (
        reverse("certificates:verify", args=[row.certificate_id])
        if verify
        else reverse("certificates:mine")
    )
    user = None if verify else row.enrollment.trainee
    return PageSetup(
        url,
        user,
        lambda: CertificateFactory.create_batch(
            9, enrollment__trainee=row.enrollment.trainee
        ),
    )


def announcement_page(manage: bool = False) -> PageSetup:
    """Compare public grouped rows and private draft-inclusive pagination."""
    admin = UserFactory(active_admin=True)
    AnnouncementFactory(created_by=admin, published=True)
    name = "announcements:manage" if manage else "announcements:home"
    return PageSetup(
        reverse(name),
        admin if manage else None,
        lambda: AnnouncementFactory.create_batch(9, created_by=admin, published=True),
    )


def competency_page(ranking: bool = False) -> PageSetup:
    """Grow either own declarations or eligible ranked trainers in one subject."""
    subject = SubjectFactory()
    row = rated(subject, 5, 10, (4, 5))
    if ranking:
        url = reverse("competency:ranking") + f"?subject={subject.pk}"
        return PageSetup(
            url,
            UserFactory(active_admin=True),
            lambda: [rated(subject, 4, 5, (3, 4)) for _ in range(9)],
        )
    return PageSetup(
        reverse("competency:mine"),
        row.trainer,
        lambda: CompetencyFactory.create_batch(9, trainer=row.trainer),
    )


def dashboard_page(admin: bool = False) -> PageSetup:
    """Scale source tables behind the actual HTML dashboard responses."""
    data = analytics_dataset()
    actor = data["admin"] if admin else data["trainer"]
    name = "dashboards:admin" if admin else "dashboards:trainer"
    return PageSetup(reverse(name), actor, lambda: query_sources(data["trainer"], 9))
