"""Check trainer management markup without widening existing access."""

import re

import pytest
from django.template.defaultfilters import filesizeformat
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.competency.tests.factories import CompetencyFactory
from apps.core.tests.frontend_markup import assert_accessible_shell
from apps.core.tests.test_trainee_learning import learning_html
from apps.courses.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(params=("owner", "admin"))
def staff_course(client: object, request: object) -> object:
    """Exercise shared templates as both authorized management roles."""
    course = CourseFactory()
    actor = (
        course.trainer if request.param == "owner" else UserFactory(active_admin=True)
    )
    client.force_login(actor)
    return course


def _post_control(client: object, html: str, name: str, pk: int) -> None:
    """Assert rendered method and token plus the write URL's GET rejection."""
    url = reverse(name, args=[pk])
    form = re.search(
        r'<form method="post" action="' + re.escape(url) + r'">(.*?)</form>', html, re.S
    )
    assert form and 'name="csrfmiddlewaretoken"' in form[1]
    assert f'href="{url}"' not in html
    assert client.get(url).status_code == 405


def test_course_management_tables_and_status(
    client: object, staff_course: object
) -> None:
    """Show draft/published status, stations, and certificate-aware participants."""
    course = staff_course
    empty = learning_html(client, "courses:detail", (course.pk,))
    assert "No modules yet." in empty and ">Draft<" in empty
    assert "No participants." in learning_html(
        client, "courses:participants", (course.pk,)
    )
    assert ">Draft<" in learning_html(client, "courses:list")
    _post_control(client, empty, "courses:publish", course.pk)
    course.is_published = True
    course.save(update_fields=["is_published"])
    module, certificate = _course_with_completed_trainee(course)
    detail = learning_html(client, "courses:detail", (course.pk,))
    assert ">Published<" in detail and ">Interchange<" in detail
    assert "<caption>" in detail and 'scope="row"' in detail
    assert "<summary>Delete module</summary>" in detail
    _post_control(client, detail, "courses:unpublish", course.pk)
    _post_control(client, detail, "courses:module_delete", module.pk)
    people = learning_html(client, "courses:participants", (course.pk,))
    assert all(
        text in people for text in ("1 of 1", ">COMPLETED<", certificate.certificate_id)
    )


def _course_with_completed_trainee(course: object) -> tuple:
    """Populate a cross-subject module and the associated certificate."""
    module = ModuleFactory(course=course, order=1)
    module.skills.add(SkillFactory(), SkillFactory())
    enrollment = EnrollmentFactory(course=course, status="COMPLETED")
    ModuleProgressFactory(enrollment=enrollment, module=module)
    certificate = CertificateFactory(enrollment=enrollment)
    return module, certificate


def test_course_and_module_editor_markup_and_frozen_error(
    client: object, staff_course: object
) -> None:
    """Keep role-specific bound fields and render the actual freeze error."""
    course = staff_course
    module = ModuleFactory(course=course, order=1)
    for route, args in (
        ("courses:create", ()),
        ("courses:edit", (course.pk,)),
        ("courses:module_add", (course.pk,)),
        ("courses:module_edit", (module.pk,)),
    ):
        html = learning_html(client, route, args)
        if route in {"courses:create", "courses:edit"}:
            assert "Date format: YYYY-MM-DD." in html and "id_start_date_format" in html
            assert ('name="trainer"' in html) == (
                client.session["_auth_user_id"] != str(course.trainer_id)
            )
    ModuleProgressFactory(module=module, enrollment=EnrollmentFactory(course=course))
    _assert_frozen_module_error(client, module)


def _assert_frozen_module_error(client: object, module: object) -> None:
    """Render the existing domain error after an invalid reorder."""
    response = client.post(
        reverse("courses:module_edit", args=[module.pk]),
        {"title": module.title, "order": 2},
    )
    assert response.status_code == 200
    assert_accessible_shell(response.content.decode())
    assert b"Module order is frozen after course progress exists." in response.content


@pytest.mark.parametrize("kind", ("VIDEO", "PRESENTATION", "DOCUMENT"))
def test_library_upload_hints_and_actions(
    client: object, staff_course: object, settings: object, kind: str
) -> None:
    """Match rendered extensions and limits to the configured upload policy."""
    course = staff_course
    assert "No visible resources." in learning_html(client, "library:list")
    row = ResourceFactory(trainer=course.trainer, kind=kind)
    settings.LIBRARY_UPLOAD_LIMITS = {
        **settings.LIBRARY_UPLOAD_LIMITS,
        kind: 17 * 1024 * 1024,
    }
    for route, args in (("library:create", ()), ("library:edit", (row.pk,))):
        html = learning_html(client, route, args)
        assert (
            'name="kind"' in html and 'aria-describedby="id_file_upload_help"' in html
        )
        for resource_kind, extensions in settings.LIBRARY_UPLOAD_EXTENSIONS.items():
            assert ", ".join(extensions) in html
            assert filesizeformat(settings.LIBRARY_UPLOAD_LIMITS[resource_kind]) in html
    _assert_library_actions(client, row)


def _assert_library_actions(client: object, row: object) -> None:
    """Exercise both publication states and POST-only delete markup."""
    assert ">Draft<" in learning_html(client, "library:list")
    detail = learning_html(client, "library:detail", (row.pk,))
    assert "<summary>Delete resource</summary>" in detail
    _post_control(client, detail, "library:delete", row.pk)
    _post_control(client, detail, "library:publish", row.pk)
    row.is_published = True
    row.save(update_fields=["is_published"])
    published = learning_html(client, "library:detail", (row.pk,))
    assert ">Published<" in published
    _post_control(client, published, "library:unpublish", row.pk)


def test_competency_table_and_forms_keep_trainer_scope(client: object) -> None:
    """Preserve Trainer-only declarations and optional subject on edit."""
    trainer = UserFactory(approved_trainer=True)
    client.force_login(trainer)
    assert "Station master" in learning_html(client, "trainer_home")
    assert "No declarations." in learning_html(client, "competency:mine")
    row = CompetencyFactory(trainer=trainer, proficiency=4)
    html = learning_html(client, "competency:mine")
    assert '<meter min="0" max="5" value="4"' in html and "4 of 5" in html
    _post_control(client, html, "competency:remove", row.pk)
    assert 'name="subject"' in learning_html(client, "competency:add")
    assert 'name="subject"' not in learning_html(client, "competency:edit", (row.pk,))
    client.force_login(UserFactory(active_admin=True))
    for name, args in (
        ("mine", ()),
        ("add", ()),
        ("edit", (row.pk,)),
        ("remove", (row.pk,)),
    ):
        assert client.get(reverse(f"competency:{name}", args=args)).status_code == 403


def test_other_trainer_cannot_manage_shared_published_objects(client: object) -> None:
    """Preserve shared reads and hide another owner's management endpoints."""
    course = CourseFactory(is_published=True)
    module = ModuleFactory(course=course)
    resource = ResourceFactory(trainer=course.trainer, is_published=True)
    client.force_login(UserFactory(approved_trainer=True))
    for path, row, edit in (
        ("courses:detail", course, "Edit course"),
        ("library:detail", resource, "Edit resource"),
    ):
        assert edit not in learning_html(client, path, (row.pk,))
    _assert_shared_editor_access(client, course, module, resource)


def _assert_shared_editor_access(
    client: object, course: object, module: object, resource: object
) -> None:
    """Check the same object URLs as other trainer and as administrator."""
    for path, row in (
        ("courses:edit", course),
        ("courses:participants", course),
        ("courses:module_add", course),
        ("courses:module_edit", module),
        ("library:edit", resource),
    ):
        url = reverse(path, args=[row.pk])
        assert client.get(url).status_code == 404
        other = client.session["_auth_user_id"]
        client.force_login(UserFactory(active_admin=True))
        assert client.get(url).status_code == 200
        client.force_login(type(course.trainer).objects.get(pk=other))
