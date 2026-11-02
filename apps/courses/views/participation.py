"""Keep enrollment and station progress scoped to the authenticated trainee."""

from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.core.form_views import action_response
from apps.courses import selectors, services


@role_required(UserRole.TRAINEE)
@require_POST
def enroll(request: HttpRequest, pk: int) -> HttpResponse:
    """Enroll only the current trainee in a visible course."""
    course = get_object_or_404(selectors.visible_courses(request.user), pk=pk)
    return action_response(
        request,
        partial(services.enroll, request.user, course),
        reverse("courses:detail", args=[pk]),
    )


@role_required(UserRole.TRAINEE)
@require_POST
def drop(request: HttpRequest, pk: int) -> HttpResponse:
    """Resolve enrollment ownership before invoking the transition service."""
    enrollment = get_object_or_404(selectors.enrollments_for(request.user), pk=pk)
    return action_response(
        request,
        partial(services.drop, request.user, enrollment),
        reverse("courses:my_courses"),
    )


@role_required(UserRole.TRAINEE)
@require_POST
def complete_module(request: HttpRequest, pk: int, module_id: int) -> HttpResponse:
    """Hide wrong-course modules and other trainees' progress IDs."""
    enrollment = get_object_or_404(selectors.enrollments_for(request.user), pk=pk)
    module = get_object_or_404(selectors.enrollment_modules(enrollment), pk=module_id)
    return action_response(
        request,
        partial(services.complete_module, request.user, enrollment, module),
        reverse("courses:detail", args=[enrollment.course_id]),
    )


@role_required(UserRole.TRAINEE)
@require_safe
def my_courses(request: HttpRequest) -> HttpResponse:
    """Expose only this trainee's annotated participation history."""
    return render(
        request,
        "courses/my_courses.html",
        {"enrollments": selectors.enrollments_for(request.user)},
    )


@role_required(UserRole.TRAINEE)
@require_safe
def station_map(request: HttpRequest) -> HttpResponse:
    """Render the handoff dataclasses as unstyled nested lists."""
    return render(
        request,
        "courses/station_map.html",
        {"lines": selectors.station_map_for(request.user)},
    )
