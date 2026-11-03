"""Verify rendered trainee states and navigation with the real views."""

import re

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.core.tests.frontend_markup import assert_accessible_shell
from apps.core.tests.page_learning import course_list
from apps.core.tests.query_pages import assert_stable_page
from apps.courses.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


def learning_html(client: object, name: str, args: tuple = ()) -> str:
    """Verify the shared accessibility contract on each actual response."""
    response = client.get(reverse(name, args=args))
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert_accessible_shell(html)
    return html


def test_empty_trainee_learning_pages(client: object) -> None:
    """Offer meaningful empty states across the trainee network."""
    client.force_login(UserFactory(approved_trainee=True))
    for route, text in (
        ("trainee_home", "You are not enrolled in a course yet"),
        ("courses:list", "No visible courses"),
        ("courses:my_courses", "No enrollments"),
        ("courses:station_map", "No active or completed enrollments"),
        ("library:list", "No visible resources"),
        ("catalog:subject_list", "No subjects yet"),
    ):
        assert text in learning_html(client, route)


def test_active_detail_and_map_use_the_same_station_states(client: object) -> None:
    """Show exactly one current action and every station in both map forms."""
    enrollment = EnrollmentFactory(course__is_published=True)
    done, current, locked = [
        ModuleFactory(course=enrollment.course, order=i) for i in range(1, 4)
    ]
    ModuleProgressFactory(enrollment=enrollment, module=done)
    client.force_login(enrollment.trainee)
    detail = learning_html(client, "courses:detail", (enrollment.course_id,))
    assert all(f">{state}</span>" in detail for state in ("DONE", "CURRENT", "LOCKED"))
    assert detail.count("Mark complete") == 1
    assert (
        reverse("courses:complete_module", args=[enrollment.pk, current.pk]) in detail
    )
    assert (
        reverse("courses:complete_module", args=[enrollment.pk, locked.pk])
        not in detail
    )
    assert ">Drop course<" in detail and ">Enroll<" not in detail
    courses = learning_html(client, "courses:my_courses")
    assert 'value="1" max="3"' in courses and "1 of 3 modules" in courses
    assert "Your network" in learning_html(client, "trainee_home")
    map_html = learning_html(client, "courses:station_map")
    svg, fallback = map_html.split("</svg>", 1)
    assert 'role="img"' in svg and "<title id=" in svg and "<desc id=" in svg
    assert (
        len(re.findall(r'aria-label="[^"]+state: (?:done|current|locked)"', svg)) == 3
    )
    assert all(
        module.title in svg and module.title in fallback
        for module in (done, current, locked)
    )


@pytest.mark.parametrize("status", ("ACTIVE", "COMPLETED", "DROPPED"))
def test_course_detail_preserves_enrollment_visibility_and_actions(
    client: object, status: str
) -> None:
    """Keep unpublished enrollments visible and expose only permitted actions."""
    enrollment = EnrollmentFactory(
        course__is_published=status == "DROPPED", status=status
    )
    ModuleFactory(course=enrollment.course)
    client.force_login(enrollment.trainee)
    if status == "COMPLETED":
        certificate = CertificateFactory(enrollment=enrollment)
    html = learning_html(client, "courses:detail", (enrollment.course_id,))
    assert (">Resume<" in html) == (status == "DROPPED")
    assert (">Drop course<" in html) == (status == "ACTIVE")
    assert (">Mark complete<" in html) == (status == "ACTIVE")
    if status == "COMPLETED":
        assert reverse("certificates:download", args=[certificate.pk]) in html
    open_course = CourseFactory(is_published=True)
    assert ">Enroll<" in learning_html(client, "courses:detail", (open_course.pk,))


@pytest.mark.parametrize("kind", ("VIDEO", "PDF"))
def test_library_uses_native_video_or_attachment(client: object, kind: str) -> None:
    """Keep the private download route and show only the existing filters."""
    resource = ResourceFactory(kind=kind, is_published=True)
    client.force_login(UserFactory(approved_trainee=True))
    listing = learning_html(client, "library:list")
    assert 'name="subject"' in listing and 'name="kind"' in listing
    assert 'name="course"' not in listing
    html = learning_html(client, "library:detail", (resource.pk,))
    url = reverse("library:download", args=[resource.pk])
    assert ('<video class="resource-video" controls preload="metadata"' in html) == (
        kind == "VIDEO"
    )
    assert f'href="{url}"' in html


def test_trainee_home_query_count_is_constant(client: object) -> None:
    """Compare populated trainee landing responses at one and ten courses."""
    assert_stable_page(client, "trainee learning home", course_list("trainee_home"))


@pytest.mark.parametrize(
    ("status", "buttons"),
    (
        (None, {"enroll": "Enroll"}),
        ("DROPPED", {"enroll": "Resume"}),
        ("ACTIVE", {"drop": "Drop course", "complete_module": "Mark complete"}),
    ),
)
def test_enrollment_actions_are_csrf_protected_post_forms(
    client: object, status: str | None, buttons: dict
) -> None:
    """Expose only the actor's permitted POST controls in the course detail."""
    user = UserFactory(approved_trainee=True)
    course = CourseFactory(is_published=True)
    module = ModuleFactory(course=course)
    enrollment = (
        EnrollmentFactory(trainee=user, course=course, status=status)
        if status
        else None
    )
    client.force_login(user)
    html = learning_html(client, "courses:detail", (course.pk,))
    urls = {"enroll": reverse("courses:enroll", args=[course.pk])}
    if enrollment:
        urls["drop"] = reverse("courses:drop", args=[enrollment.pk])
        urls["complete_module"] = reverse(
            "courses:complete_module", args=[enrollment.pk, module.pk]
        )
    for name, url in urls.items():
        assert client.get(url).status_code == 405
        _assert_action_form(html, url, buttons.get(name))


def _assert_action_form(html: str, url: str, label: str | None) -> None:
    """Check the rendered action shape without depending on the CSRF value."""
    assert f'href="{url}"' not in html
    forms = re.findall(
        r'<form method="post" action="' + re.escape(url) + r'">(.*?)</form>',
        html,
        re.S,
    )
    assert len(forms) == (label is not None)
    if label:
        assert 'name="csrfmiddlewaretoken"' in forms[0]
        assert f">{label}</button>" in forms[0]


def test_course_enrollment_controls_are_trainee_only(client: object) -> None:
    """Keep participation actions out of staff and anonymous responses."""
    course = CourseFactory(is_published=True)
    for actor in (None, course.trainer, UserFactory(active_admin=True)):
        if actor:
            client.force_login(actor)
        response = client.get(reverse("courses:detail", args=[course.pk]))
        for label in (b"Enroll", b"Resume", b"Drop course", b"Mark complete"):
            assert b">" + label + b"</button>" not in response.content
