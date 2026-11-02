"""Connect authoring, learning, certification and reporting using real HTTP."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.assessments.models import Attempt
from apps.certificates.models import Certificate
from apps.core.demo_files import demo_pdf
from apps.core.tests.journeys.helpers import learning_course, post, questionnaire
from apps.courses.models import Enrollment
from apps.library.models import LibraryResource

pytestmark = pytest.mark.django_db


def test_j1_happy_path(journey: tuple) -> None:
    """Prove the complete learning journey yields durable certification and reports."""
    admin, trainer, staff, trainee, learner, subject = journey
    post(
        staff,
        "competency:add",
        {"subject": subject.pk, "proficiency": 4, "years_experience": 6},
    )
    course, modules = learning_course(staff, subject.pk)
    quiz, question = questionnaire(staff, course)
    _resource(staff, course)
    _learn(learner, course, modules, (quiz, question))
    certificate = Certificate.objects.get(enrollment__trainee=trainee)
    response = learner.get(reverse("certificates:download", args=[certificate.pk]))
    assert response["Content-Disposition"].startswith("attachment;")
    assert b"".join(response.streaming_content).startswith(b"%PDF-")
    public = Client().get(
        reverse("certificates:verify", args=[certificate.certificate_id])
    )
    assert public.status_code == 200 and trainee.first_name.encode() in public.content
    _feedback_and_reports(journey, course)


def _resource(staff: Client, course: object) -> None:
    """Publish and retrieve a genuine PDF through library HTTP endpoints."""
    post(
        staff,
        "library:create",
        {
            "title": "Journey PDF",
            "description": "Practice",
            "subject": course.subject_id,
            "course": course.pk,
            "kind": "DOCUMENT",
            "file": demo_pdf(),
        },
    )
    resource = LibraryResource.objects.get(title="Journey PDF")
    post(staff, "library:publish", args=(resource.pk,))


def _learn(learner: Client, course: object, modules: tuple, assessment: tuple) -> None:
    """Complete ordered modules, then pass the quiz without calling domain services."""
    quiz, question = assessment
    post(
        learner, "profiles:trainee_edit", {"bio": "Ready to learn", "interests": "Data"}
    )
    post(learner, "courses:enroll", args=(course.pk,))
    enrollment = Enrollment.objects.get(course=course)
    for module in modules:
        post(learner, "courses:complete_module", args=(enrollment.pk, module.pk))
    post(learner, "assessments:start", args=(quiz.pk,))
    attempt = Attempt.objects.get(trainee=enrollment.trainee)
    response = learner.get(reverse("assessments:take", args=[attempt.pk]))
    assert b"Which is safe?" in response.content
    post(
        learner,
        "assessments:take",
        {f"question_{question.pk}": question.options.get(is_correct=True).pk},
        (attempt.pk,),
    )
    result = learner.get(reverse("assessments:result", args=[attempt.pk]))
    assert b"Passed" in result.content and b"100.00%" in result.content


def _feedback_and_reports(journey: tuple, course: object) -> None:
    """Check anonymous feedback, dashboard totals, ranking and public announcements."""
    admin, trainer, staff, trainee, learner, subject = journey
    post(
        learner,
        "feedback:course_submit",
        {"rating": 5, "comment": "Helpful practice"},
        (course.pk,),
    )
    summary = staff.get(reverse("feedback:course_summary", args=[course.pk]))
    assert (
        b"Helpful practice" in summary.content
        and trainee.username.encode() not in summary.content
    )
    dashboard = admin.get(reverse("dashboards:admin")).context["dashboard"]
    assert dashboard.certificates_total == dashboard.enrollments_total == 1
    assert dashboard.assessments.submitted_attempts == 1
    ranking = admin.get(reverse("competency:ranking"), {"subject": subject.pk})
    assert trainer.first_name.encode() in ranking.content
    _announcement(admin)


def _announcement(admin: Client) -> None:
    """Publish new library content to the public board through Admin HTTP."""
    post(
        admin,
        "announcements:create",
        {
            "title": "New journey workbook",
            "body": "Read Journey PDF",
            "category": "NEW_CONTENT",
        },
    )
    from apps.announcements.models import Announcement

    row = Announcement.objects.get(title="New journey workbook")
    post(admin, "announcements:publish", args=(row.pk,))
    assert b"New journey workbook" in Client().get("/").content
