"""Expose explicit role and ownership boundaries for profile pages."""

from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.core.form_views import FormAction, form_response
from apps.profiles import selectors, services
from apps.profiles.forms import AccountForm, TraineeProfileForm, TrainerProfileForm


@role_required(*UserRole.values)
def account_edit(request: HttpRequest) -> HttpResponse:
    """Let all approved roles maintain their own contact information."""
    action = FormAction(
        AccountForm,
        partial(services.update_account, request.user),
        request.user,
        reverse("profiles:account_edit"),
        "Account details",
    )
    return form_response(request, action)


@role_required(*UserRole.values)
@require_safe
def trainee_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Return 404 when a trainee profile is outside the actor's visibility."""
    profile = get_object_or_404(selectors.visible_trainees(request.user), pk=pk)
    return render(request, "profiles/trainee.html", {"profile": profile})


@role_required(*UserRole.values)
@require_safe
def trainer_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Publish trainer details within the approved portal."""
    profile = get_object_or_404(selectors.visible_trainers(request.user), pk=pk)
    return render(request, "profiles/trainer.html", {"profile": profile})


@role_required(UserRole.TRAINEE)
def trainee_edit(request: HttpRequest) -> HttpResponse:
    """Create the current role's profile only when its owner needs it."""
    profile = services.ensure_trainee_profile(request.user)
    action = FormAction(
        TraineeProfileForm,
        partial(services.update_trainee_profile, profile),
        profile,
        reverse("profiles:trainee_detail", args=[profile.pk]),
        "Trainee profile",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER)
def trainer_edit(request: HttpRequest) -> HttpResponse:
    """Keep trainer editing scoped to the current account."""
    profile = services.ensure_trainer_profile(request.user)
    action = FormAction(
        TrainerProfileForm,
        partial(services.update_trainer_profile, profile),
        profile,
        reverse("profiles:trainer_detail", args=[profile.pk]),
        "Trainer profile",
    )
    return form_response(request, action)


@role_required(*UserRole.values)
@require_safe
def profile_list(request: HttpRequest) -> HttpResponse:
    """Make authorized detail pages discoverable through a role-aware directory."""
    return render(
        request,
        "profiles/list.html",
        {
            "trainees": selectors.visible_trainees(request.user),
            "trainers": selectors.visible_trainers(request.user),
        },
    )
