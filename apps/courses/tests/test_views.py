"""Exercise course/module forms and trainee progress as complete HTTP flows."""

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.courses.models import Course, Enrollment, Module
from apps.courses.tests.factories import CourseFactory, ModuleFactory

pytestmark = pytest.mark.django_db


def form_data(subject: object) -> dict:
    """Use valid deterministic form dates in management view tests."""
    return {
        "title": "HTTP course",
        "description": "Details",
        "subject": subject.pk,
        "start_date": "2026-01-01",
        "end_date": "2026-02-01",
    }


def test_trainer_course_form_writes(client: Client) -> None:
    """Persist allowed edits while ignoring forged publication and owner fields."""
    owner = UserFactory(approved_trainer=True)
    other = UserFactory(approved_trainer=True)
    subject = SubjectFactory()
    client.force_login(owner)
    data = dict(form_data(subject), trainer=other.pk, is_published=True)
    assert client.post(reverse("courses:create"), data).status_code == 302
    course = Course.objects.get(title="HTTP course")
    assert course.trainer == owner and not course.is_published
    data["title"] = "Updated HTTP course"
    assert (
        client.post(reverse("courses:edit", args=[course.pk]), data).status_code == 302
    )
    course.refresh_from_db()
    assert course.title == data["title"]


def test_trainer_module_form_writes(client: Client) -> None:
    """Persist module edits and deletions through the owning trainer's forms."""
    course = CourseFactory()
    client.force_login(course.trainer)
    add_url = reverse("courses:module_add", args=[course.pk])
    assert client.post(add_url, {"title": "One", "order": 1}).status_code == 302
    module = Module.objects.get(course=course)
    edit_url = reverse("courses:module_edit", args=[module.pk])
    assert client.post(edit_url, {"title": "Updated", "order": 1}).status_code == 302
    module.refresh_from_db()
    assert module.title == "Updated"
    delete_url = reverse("courses:module_delete", args=[module.pk])
    assert client.post(delete_url).status_code == 302
    assert not Module.objects.exists()


def test_enroll_complete_drop_resume_http_flow(client: Client) -> None:
    """Keep progress across drops without triggering quiz-dependent completion."""
    course = CourseFactory(is_published=True)
    module = ModuleFactory(course=course, order=1)
    trainee = UserFactory(approved_trainee=True)
    client.force_login(trainee)
    assert client.post(reverse("courses:enroll", args=[course.pk])).status_code == 302
    enrollment = Enrollment.objects.get(trainee=trainee)
    completion = reverse("courses:complete_module", args=[enrollment.pk, module.pk])
    assert client.post(completion).status_code == 302
    assert client.post(completion).status_code == 302
    enrollment.refresh_from_db()
    assert enrollment.status == "ACTIVE" and enrollment.progress.count() == 1
    assert client.post(reverse("courses:drop", args=[enrollment.pk])).status_code == 302
    assert client.post(reverse("courses:enroll", args=[course.pk])).status_code == 302
    enrollment.refresh_from_db()
    assert enrollment.status == "ACTIVE" and enrollment.progress.count() == 1


def test_duplicate_module_order_is_form_feedback(client: Client) -> None:
    """Render service order conflicts on the form instead of producing a 500."""
    module = ModuleFactory(order=1)
    client.force_login(module.course.trainer)
    response = client.post(
        reverse("courses:module_add", args=[module.course_id]),
        {"title": "Duplicate", "order": 1},
    )
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert Module.objects.count() == 1


def test_valid_csrf_token_allows_course_form_post() -> None:
    """Keep server-rendered CSRF fields functional with HttpOnly cookie settings."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(UserFactory(approved_trainer=True))
    url = reverse("courses:create")
    assert client.get(url).status_code == 200
    data = dict(
        form_data(SubjectFactory()),
        csrfmiddlewaretoken=client.cookies["csrftoken"].value,
    )
    assert client.post(url, data).status_code == 302


def _order_race_hook() -> Any:
    """Insert a competing module only after service full_clean has succeeded."""
    real_clean = Module.full_clean

    def insert_competitor(module: Module, *args: Any, **kwargs: Any) -> None:
        """Exercise the real unique constraint rather than mock its exception."""
        real_clean(module, *args, **kwargs)
        if module.title == "Race" and not kwargs:
            ModuleFactory(course=module.course, order=module.order)

    return insert_competitor


def test_module_order_database_race_is_form_feedback(
    client: Client, monkeypatch: Any
) -> None:
    """Recover an order collision that appears after form and service validation."""
    course = CourseFactory()
    client.force_login(course.trainer)
    monkeypatch.setattr(Module, "full_clean", _order_race_hook())
    response = client.post(
        reverse("courses:module_add", args=[course.pk]), {"title": "Race", "order": 1}
    )
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert not Module.objects.exists()
