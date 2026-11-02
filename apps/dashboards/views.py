"""Limit aggregate analytics to the explicit Admin or owning trainer roles."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.dashboards import selectors


@role_required(UserRole.ADMIN)
@require_safe
def admin(request: HttpRequest) -> HttpResponse:
    """Keep organization-wide figures out of trainee/trainer pages."""
    return render(
        request, "dashboards/admin.html", {"dashboard": selectors.admin_dashboard()}
    )


@role_required(UserRole.TRAINER)
@require_safe
def trainer(request: HttpRequest) -> HttpResponse:
    """Never accept a trainer ID that could expose another trainer's courses."""
    return render(
        request,
        "dashboards/trainer.html",
        {"dashboard": selectors.trainer_dashboard(request.user)},
    )
