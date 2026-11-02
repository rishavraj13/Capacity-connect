"""Coordinate trainer declaration forms and Admin-only ranking lookup."""

from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.competency import selectors, services
from apps.competency.forms import CompetencyForm, DeclarationForm, RankingForm
from apps.core.form_views import FormAction, action_response, form_response


def _declare(user: object, data: dict) -> object:
    """Adapt form input to the subject-explicit service signature."""
    return services.declare_competency(user, data["subject"], data)


@role_required(UserRole.TRAINER)
@require_safe
def mine(request: HttpRequest) -> HttpResponse:
    """List only the trainer's own retained declarations."""
    return render(
        request,
        "competency/mine.html",
        {"competencies": selectors.competencies_for(request.user)},
    )


@role_required(UserRole.TRAINER)
def add(request: HttpRequest) -> HttpResponse:
    """Keep declaration ownership assigned by the service rather than the POST."""
    return form_response(
        request,
        FormAction(
            DeclarationForm,
            partial(_declare, request.user),
            success_url=reverse("competency:mine"),
            title="Declare competency",
        ),
    )


@role_required(UserRole.TRAINER)
def edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Hide other trainers' declaration IDs before form binding."""
    row = get_object_or_404(selectors.competencies_for(request.user), pk=pk)
    return form_response(
        request,
        FormAction(
            CompetencyForm,
            partial(services.update_competency, request.user, row),
            row,
            reverse("competency:mine"),
            "Edit competency",
        ),
    )


@role_required(UserRole.TRAINER)
@require_POST
def remove(request: HttpRequest, pk: int) -> HttpResponse:
    """Require POST and ownership before deleting a declaration."""
    row = get_object_or_404(selectors.competencies_for(request.user), pk=pk)
    return action_response(
        request,
        partial(services.remove_competency, request.user, row),
        reverse("competency:mine"),
    )


@role_required(UserRole.ADMIN)
@require_safe
def ranking(request: HttpRequest) -> HttpResponse:
    """Keep ranking read-only and limited to the Admin's selected subject."""
    form = RankingForm(request.GET or None)
    subject = form.cleaned_data.get("subject") if form.is_valid() else None
    return render(
        request,
        "competency/ranking.html",
        {
            "form": form,
            "ranking": selectors.rank_trainers_for(subject) if subject else (),
        },
    )
