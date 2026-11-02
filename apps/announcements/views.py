"""Expose a public board and thin Admin-only manual authoring controllers."""

from functools import partial

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.constants import ROLE_HOME_URL_NAMES, UserRole
from apps.accounts.permissions import role_required
from apps.announcements import selectors, services
from apps.announcements.constants import PAGE_SIZE, Category
from apps.announcements.forms import AnnouncementForm
from apps.core.form_views import FormAction, action_response, form_response


@require_safe
def home(request: HttpRequest) -> HttpResponse:
    """Show the same published board to anonymous and authenticated visitors."""
    landing = (
        ROLE_HOME_URL_NAMES.get(getattr(request.user, "role", None))
        if request.user.is_authenticated
        else None
    )
    return render(
        request,
        "announcements/home.html",
        {"board": selectors.board(), "landing": landing},
    )


@role_required(UserRole.ADMIN)
@require_safe
def manage(request: HttpRequest) -> HttpResponse:
    """Paginate Admin draft/published reads without a public draft endpoint."""
    rows = selectors.manage_list(
        request.user, request.GET.get("category", ""), request.GET.get("status", "")
    )
    return render(
        request,
        "announcements/manage.html",
        {
            "page": Paginator(rows, PAGE_SIZE).get_page(request.GET.get("page")),
            "categories": Category.choices,
        },
    )


@role_required(UserRole.ADMIN)
def create(request: HttpRequest) -> HttpResponse:
    """Create manual content as a draft through shared domain form feedback."""
    return form_response(
        request,
        FormAction(
            AnnouncementForm,
            partial(services.create, request.user),
            success_url=reverse("announcements:manage"),
            title="Create announcement",
        ),
    )


@role_required(UserRole.ADMIN)
def edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Resolve Admin scope before binding content changes."""
    row = get_object_or_404(selectors.manage_list(request.user), pk=pk)
    return form_response(
        request,
        FormAction(
            AnnouncementForm,
            partial(services.update, request.user, row),
            row,
            reverse("announcements:manage"),
            "Edit announcement",
        ),
    )


def _action(request: HttpRequest, pk: int, operation: object) -> HttpResponse:
    """Share object scope and redirect wiring while services own publication rules."""
    row = get_object_or_404(selectors.manage_list(request.user), pk=pk)
    return action_response(
        request, partial(operation, request.user, row), reverse("announcements:manage")
    )


@role_required(UserRole.ADMIN)
@require_POST
def publish(request: HttpRequest, pk: int) -> HttpResponse:
    """Keep publication state transitions CSRF-protected and POST-only."""
    return _action(request, pk, services.publish)


@role_required(UserRole.ADMIN)
@require_POST
def unpublish(request: HttpRequest, pk: int) -> HttpResponse:
    """Withdraw public content only through the explicit Admin action."""
    return _action(request, pk, services.unpublish)


@role_required(UserRole.ADMIN)
@require_POST
def delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Keep destructive content actions out of safe methods."""
    return _action(request, pk, services.delete)
