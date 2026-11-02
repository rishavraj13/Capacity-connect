"""Coordinate trainee editing and staff-only anonymized summary pages."""

from functools import partial

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_safe,
)

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.core.form_views import FormAction, action_response, form_response
from apps.feedback import selectors, services
from apps.feedback.forms import FeedbackForm


def _write(trainee: object, target: object, course: bool, data: dict) -> object:
    """Adapt a grouped form to the explicit target service boundary."""
    operation = (
        services.submit_course_feedback if course else services.submit_resource_feedback
    )
    return operation(trainee, target, data["rating"], data["comment"])


@role_required(UserRole.TRAINEE)
@require_http_methods(["GET", "POST"])
def submit(request: HttpRequest, pk: int, course: bool) -> HttpResponse:
    """Hide ineligible target IDs before binding an own-feedback form."""
    target = get_object_or_404(selectors.eligible_targets(request.user, course), pk=pk)
    row = (
        selectors.feedback_for_trainee(request.user)
        .filter(**selectors.target_filter(target))
        .first()
    )
    action = FormAction(
        FeedbackForm,
        partial(_write, request.user, target, course),
        row,
        reverse("feedback:mine"),
        "Your feedback",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINEE)
@require_POST
def delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Return 404 for another trainee's feedback before attempting deletion."""
    row = get_object_or_404(selectors.feedback_for_trainee(request.user), pk=pk)
    return action_response(
        request,
        partial(services.delete_feedback, request.user, row),
        reverse("feedback:mine"),
    )


@role_required(UserRole.TRAINEE)
@require_safe
def mine(request: HttpRequest) -> HttpResponse:
    """Expose own course/resource edit links without private staff summaries."""
    return render(
        request,
        "feedback/mine.html",
        {"feedback": selectors.feedback_for_trainee(request.user)},
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_safe
def summary(request: HttpRequest, pk: int, course: bool) -> HttpResponse:
    """Keep author identity decisions in the selector DTO contract."""
    target = get_object_or_404(selectors.managed_targets(request.user, course), pk=pk)
    page = selectors.feedback_page(request.user, target, request.GET.get("page", 1))
    if page is None:
        raise Http404
    return render(
        request,
        "feedback/summary.html",
        {"target": target, "page": page, "summary": selectors.feedback_summary(target)},
    )
