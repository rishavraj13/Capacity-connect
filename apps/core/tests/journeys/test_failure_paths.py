"""Reject lifecycle and authorization failures through actual browser requests."""

from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.assessments.models import Attempt
from apps.assessments.tests.factories import MOMENT
from apps.core import clock
from apps.core.tests.journeys.helpers import (
    PASSWORD,
    learning_course,
    post,
    questionnaire,
    register,
)
from apps.courses.models import Enrollment, ModuleProgress

pytestmark = pytest.mark.django_db


def test_j2_unapproved_wrong_role_and_rejected_session(journey: tuple) -> None:
    """Show status messages and revoke an already authenticated rejected user."""
    admin, _, _, trainee, learner, _ = journey
    visitor = Client()
    register("pending")
    response = visitor.post(
        reverse("login"), {"username": "pending", "password": PASSWORD}
    )
    assert (
        response.status_code == 200
        and b"awaiting administrator approval" in response.content.lower()
    ), response.context["form"].errors
    assert learner.get(reverse("dashboards:admin")).status_code == 403
    post(admin, "admin_reject_user", args=(trainee.pk,))
    assert learner.get(reverse("profiles:trainee_edit")).status_code in {302, 403}
    assert not User.objects.get(pk=trainee.pk).is_active


def test_j2_late_submission_and_third_attempt_refused(
    journey: tuple, monkeypatch: object
) -> None:
    """Persist TIMED_OUT over HTTP and refuse a third lifecycle at quota two."""
    _, _, staff, trainee, learner, subject = journey
    course, _ = learning_course(staff, subject.pk)
    quiz, _ = questionnaire(staff, course)
    post(learner, "courses:enroll", args=(course.pk,))
    post(learner, "assessments:start", args=(quiz.pk,))
    attempt = Attempt.objects.get(trainee=trainee)
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(minutes=6))
    post(learner, "assessments:take", args=(attempt.pk,))
    result = learner.get(reverse("assessments:result", args=[attempt.pk]))
    assert b"TIMED_OUT" in result.content and b"Not passed" in result.content
    post(learner, "assessments:start", args=(quiz.pk,))
    second = Attempt.objects.filter(trainee=trainee).latest("pk")
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(minutes=12))
    post(learner, "assessments:take", args=(second.pk,))
    response = learner.post(reverse("assessments:start", args=[quiz.pk]), follow=True)
    assert b"Maximum attempts reached" in response.content
    assert Attempt.objects.filter(trainee=trainee).count() == 2


def test_j2_module_skip_and_dropped_trainee_refused(journey: tuple) -> None:
    """Keep out-of-order progress absent and dropped participation inactive."""
    _, _, staff, _, learner, subject = journey
    course, modules = learning_course(staff, subject.pk)
    quiz, _ = questionnaire(staff, course)
    post(learner, "courses:enroll", args=(course.pk,))
    enrollment = Enrollment.objects.get(course=course)
    response = learner.post(
        reverse("courses:complete_module", args=[enrollment.pk, modules[1].pk]),
        follow=True,
    )
    assert b"Complete modules in order" in response.content
    assert not ModuleProgress.objects.exists()
    post(learner, "courses:drop", args=(enrollment.pk,))
    response = learner.get(reverse("courses:detail", args=[course.pk]))
    assert b"DROPPED" in response.content
    assert learner.post(reverse("assessments:start", args=[quiz.pk])).status_code == 404
    response = learner.post(
        reverse("courses:complete_module", args=[enrollment.pk, modules[0].pk]),
        follow=True,
    )
    assert b"Enrollment must be active" in response.content
    assert not ModuleProgress.objects.exists()
