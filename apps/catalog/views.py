"""Declare catalog roles while delegating reads and writes to their layers."""

from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.catalog import selectors, services
from apps.catalog.forms import SkillForm, SubjectForm
from apps.core.form_views import FormAction, form_response


@role_required(*UserRole.values)
@require_safe
def subject_list(request: HttpRequest) -> HttpResponse:
    """Make the complete catalog readable to approved portal users."""
    return render(
        request, "catalog/list.html", {"subjects": selectors.subjects_with_skills()}
    )


@role_required(UserRole.ADMIN)
def subject_create(request: HttpRequest) -> HttpResponse:
    """Give administrators a validated subject creation form."""
    return form_response(
        request,
        FormAction(SubjectForm, services.create_subject, title="Create subject"),
    )


@role_required(UserRole.ADMIN)
def subject_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Keep subject lifecycle changes separate from descriptive edits."""
    subject = get_object_or_404(selectors.all_subjects(), pk=pk)
    return form_response(
        request,
        FormAction(SubjectForm, partial(services.update_subject, subject), subject),
    )


@role_required(UserRole.ADMIN)
@require_POST
def subject_deactivate(request: HttpRequest, pk: int) -> HttpResponse:
    """Require deliberate POST submission before retiring a subject."""
    services.deactivate_subject(get_object_or_404(selectors.all_subjects(), pk=pk))
    return redirect("catalog:subject_list")


@role_required(UserRole.ADMIN)
@require_POST
def subject_reactivate(request: HttpRequest, pk: int) -> HttpResponse:
    """Restore existing subject history through an explicit action."""
    services.reactivate_subject(get_object_or_404(selectors.all_subjects(), pk=pk))
    return redirect("catalog:subject_list")


@role_required(UserRole.ADMIN)
def skill_create(request: HttpRequest) -> HttpResponse:
    """Route skill creation through the active subject rule."""
    return form_response(
        request, FormAction(SkillForm, services.create_skill, title="Create skill")
    )


@role_required(UserRole.ADMIN)
def skill_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Keep skill edits within the catalog service contract."""
    skill = get_object_or_404(selectors.all_skills(), pk=pk)
    return form_response(
        request, FormAction(SkillForm, partial(services.update_skill, skill), skill)
    )


@role_required(UserRole.ADMIN)
@require_POST
def skill_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Prevent links or crawlers from deleting catalog data."""
    services.delete_skill(get_object_or_404(selectors.all_skills(), pk=pk))
    return redirect("catalog:subject_list")
