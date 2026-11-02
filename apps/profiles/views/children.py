"""Keep child record HTTP flows thin and ownership-filtered."""

from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.core.form_views import FormAction, form_response
from apps.profiles import selectors, services
from apps.profiles.forms import (
    ExternalCertificateForm,
    QualificationForm,
    WorkExperienceForm,
)
from apps.profiles.models import ExternalCertificate, Qualification, WorkExperience


def _child_form(request: HttpRequest, record: object, form_class: type) -> HttpResponse:
    """Share form presentation while keeping ownership resolution explicit."""
    destination = reverse("profiles:trainee_detail", args=[record.profile_id])
    action = FormAction(
        form_class, partial(services.save_child, record), record, destination
    )
    return form_response(request, action)


def _delete(request: HttpRequest, record: object) -> HttpResponse:
    """Preserve a stable return destination after the child row is gone."""
    profile_id = record.profile_id
    services.delete_child(record)
    return redirect("profiles:trainee_detail", pk=profile_id)


@role_required(UserRole.TRAINEE)
def qualification_create(request: HttpRequest) -> HttpResponse:
    """Restrict qualification create to its trainee owner."""
    profile = services.ensure_trainee_profile(request.user)
    record = Qualification(profile=profile)
    return _child_form(request, record, QualificationForm)


@role_required(UserRole.TRAINEE)
def qualification_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Restrict qualification edit to its trainee owner."""
    record = get_object_or_404(
        selectors.owned_children(request.user, Qualification), pk=pk
    )
    return _child_form(request, record, QualificationForm)


@role_required(UserRole.TRAINEE)
@require_POST
def qualification_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Restrict qualification delete to its trainee owner."""
    record = get_object_or_404(
        selectors.owned_children(request.user, Qualification), pk=pk
    )
    return _delete(request, record)


@role_required(UserRole.TRAINEE)
def experience_create(request: HttpRequest) -> HttpResponse:
    """Restrict experience create to its trainee owner."""
    profile = services.ensure_trainee_profile(request.user)
    record = WorkExperience(profile=profile)
    return _child_form(request, record, WorkExperienceForm)


@role_required(UserRole.TRAINEE)
def experience_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Restrict experience edit to its trainee owner."""
    record = get_object_or_404(
        selectors.owned_children(request.user, WorkExperience), pk=pk
    )
    return _child_form(request, record, WorkExperienceForm)


@role_required(UserRole.TRAINEE)
@require_POST
def experience_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Restrict experience delete to its trainee owner."""
    record = get_object_or_404(
        selectors.owned_children(request.user, WorkExperience), pk=pk
    )
    return _delete(request, record)


@role_required(UserRole.TRAINEE)
def certificate_create(request: HttpRequest) -> HttpResponse:
    """Restrict certificate create to its trainee owner."""
    profile = services.ensure_trainee_profile(request.user)
    record = ExternalCertificate(profile=profile)
    return _child_form(request, record, ExternalCertificateForm)


@role_required(UserRole.TRAINEE)
def certificate_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Restrict certificate edit to its trainee owner."""
    record = get_object_or_404(
        selectors.owned_children(request.user, ExternalCertificate), pk=pk
    )
    return _child_form(request, record, ExternalCertificateForm)


@role_required(UserRole.TRAINEE)
@require_POST
def certificate_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Restrict certificate delete to its trainee owner."""
    record = get_object_or_404(
        selectors.owned_children(request.user, ExternalCertificate), pk=pk
    )
    return _delete(request, record)
