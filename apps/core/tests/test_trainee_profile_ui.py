"""Check certificates, feedback, and profile controls in rendered trainee pages."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.core.tests.frontend_markup import assert_accessible_shell
from apps.core.tests.query_pages import PageSetup, assert_stable_page
from apps.core.tests.test_trainee_learning import learning_html
from apps.courses.tests.factories import EnrollmentFactory
from apps.feedback.tests.factories import FeedbackFactory
from apps.library.tests.factories import ResourceFactory
from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    QualificationFactory,
    TraineeProfileFactory,
    TrainerProfileFactory,
    WorkExperienceFactory,
)

pytestmark = pytest.mark.django_db


def test_empty_trainee_account_pages(client: object) -> None:
    """Give empty histories and lists readable exits."""
    client.force_login(UserFactory(approved_trainee=True))
    for route, expected in (
        ("assessments:mine", "No enrolled assessments."),
        ("assessments:history", "No attempts."),
        ("certificates:mine", "Complete a course to earn your first certificate."),
        ("feedback:mine", "No feedback yet."),
    ):
        assert expected in learning_html(client, route)


def test_earned_certificate_links_to_private_pdf(client: object) -> None:
    """Show the formal certificate metadata and existing download action."""
    certificate = CertificateFactory()
    client.force_login(certificate.enrollment.trainee)
    html = learning_html(client, "certificates:mine")
    assert (
        certificate.certificate_id in html and "Grade" in html and "Issue date" in html
    )
    assert reverse("certificates:download", args=[certificate.pk]) in html


def test_feedback_radios_errors_and_delete_confirmation(client: object) -> None:
    """Label each rating, link errors, and keep deletion POST-only."""
    enrollment = EnrollmentFactory(status="COMPLETED")
    feedback = FeedbackFactory(author=enrollment.trainee, course=enrollment.course)
    client.force_login(enrollment.trainee)
    route = reverse("feedback:course_submit", args=[enrollment.course_id])
    html = learning_html(client, "feedback:course_submit", (enrollment.course_id,))
    assert "<legend>Rating</legend>" in html
    assert all(f"{value} of 5" in html for value in range(1, 6))
    assert "2000 characters" in html
    response = client.post(route, {"rating": 6, "comment": "Example"})
    assert response.status_code == 200
    html = response.content.decode()
    assert_accessible_shell(html)
    assert 'href="#id_rating"' in html and 'aria-describedby="id_rating_error"' in html
    listing = learning_html(client, "feedback:mine")
    delete = reverse("feedback:delete", args=[feedback.pk])
    assert "<summary>Delete feedback</summary>" in listing
    assert f'<form method="post" action="{delete}">' in listing
    assert "Confirm delete" in listing and client.get(delete).status_code == 405


def test_profile_records_and_private_file_help(client: object) -> None:
    """Keep child routes scoped and associate upload help with the file field."""
    profile = TraineeProfileFactory()
    client.force_login(profile.user)
    assert "No records yet." in learning_html(
        client, "profiles:trainee_detail", (profile.pk,)
    )
    qualification = QualificationFactory(profile=profile)
    experience = WorkExperienceFactory(profile=profile)
    certificate = ExternalCertificateFactory(profile=profile)
    trainer = TrainerProfileFactory()
    full = learning_html(client, "profiles:trainee_detail", (profile.pk,))
    assert all(
        value in full
        for value in (qualification.degree, experience.role, certificate.title)
    )
    assert full.count("Confirm delete") == 3
    assert (
        reverse("profiles:private_file", args=["certificate", certificate.pk]) in full
    )
    assert "Edit profile" not in learning_html(
        client, "profiles:trainer_detail", (trainer.pk,)
    )
    assert "Profiles" in learning_html(client, "profiles:profile_list")


@pytest.mark.parametrize("child", ("qualification", "experience", "certificate"))
def test_profile_child_create_forms_link_errors(client: object, child: str) -> None:
    """Exercise real form controls and invalid submissions for every record type."""
    client.force_login(UserFactory(approved_trainee=True))
    name = f"profiles:{child}_create"
    html = learning_html(client, name)
    if child == "certificate":
        assert 'aria-describedby="id_file_upload_help"' in html
        assert "Allowed types: PDF, JPG, JPEG, PNG." in html
    response = client.post(reverse(name), {})
    assert response.status_code == 200
    assert_accessible_shell(response.content.decode())
    assert b"This field is required." in response.content


def _profile_routes(profile: object) -> tuple:
    """Cover editor routes absent from the existing page query recipes."""
    children = (
        ("qualification", QualificationFactory(profile=profile)),
        ("experience", WorkExperienceFactory(profile=profile)),
        ("certificate", ExternalCertificateFactory(profile=profile)),
    )
    return (
        reverse("profiles:account_edit"),
        reverse("profiles:trainee_edit"),
        *(reverse(f"profiles:{name}_create") for name, _ in children),
        *(reverse(f"profiles:{name}_edit", args=[row.pk]) for name, row in children),
    )


@pytest.mark.parametrize("index", range(8))
def test_profile_editor_query_counts_are_constant(client: object, index: int) -> None:
    """Grow a trainee's child records while reading a single editor page."""
    profile = TraineeProfileFactory()
    url = _profile_routes(profile)[index]
    setup = PageSetup(
        url, profile.user, lambda: QualificationFactory.create_batch(9, profile=profile)
    )
    assert_stable_page(client, f"trainee profile editor {index}", setup)


@pytest.mark.parametrize("target", ("course", "resource"))
def test_feedback_editor_query_counts_are_constant(client: object, target: str) -> None:
    """Keep the selected feedback edit bounded as the trainee history grows."""
    enrollment = EnrollmentFactory()
    resource = ResourceFactory(is_published=True)
    pk = enrollment.course_id if target == "course" else resource.pk
    url = reverse(f"feedback:{target}_submit", args=[pk])
    user = enrollment.trainee
    FeedbackFactory(author=user)
    setup = PageSetup(url, user, lambda: FeedbackFactory.create_batch(9, author=user))
    assert_stable_page(client, f"trainee feedback editor {target}", setup)
