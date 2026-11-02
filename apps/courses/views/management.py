"""Keep course and module controllers role-declared and ownership-filtered."""

from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.core.form_views import FormAction, action_response, form_response
from apps.courses import selectors, services
from apps.courses.forms import CourseForm, ModuleForm


@role_required(*UserRole.values)
@require_safe
def course_list(request: HttpRequest) -> HttpResponse:
    """Expose only the course rows visible to the current approved actor."""
    return render(
        request,
        "courses/list.html",
        {"courses": selectors.visible_courses(request.user)},
    )


@role_required(*UserRole.values)
@require_safe
def course_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Resolve private course visibility before rendering any station data."""
    course = get_object_or_404(selectors.course_detail(request.user, pk))
    return render(
        request, "courses/detail.html", selectors.detail_context(request.user, course)
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def course_create(request: HttpRequest) -> HttpResponse:
    """Build course ownership from the authenticated actor rather than POST flags."""
    action = FormAction(
        partial(CourseForm, actor=request.user),
        partial(services.create_course, request.user),
        success_url=reverse("courses:list"),
        title="Create course",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def course_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Return 404 before validating changes to another trainer's course."""
    course = get_object_or_404(selectors.managed_courses(request.user), pk=pk)
    action = FormAction(
        partial(CourseForm, actor=request.user),
        partial(services.update_course, request.user, course),
        course,
        reverse("courses:detail", args=[pk]),
        "Edit course",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def course_publish(request: HttpRequest, pk: int) -> HttpResponse:
    """Publish only a managed course via an explicit CSRF-protected action."""
    course = get_object_or_404(selectors.managed_courses(request.user), pk=pk)
    return action_response(
        request,
        partial(services.publish, request.user, course),
        reverse("courses:detail", args=[pk]),
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def course_unpublish(request: HttpRequest, pk: int) -> HttpResponse:
    """Withdraw new access while preserving enrolled trainees' history."""
    course = get_object_or_404(selectors.managed_courses(request.user), pk=pk)
    return action_response(
        request,
        partial(services.unpublish, request.user, course),
        reverse("courses:detail", args=[pk]),
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def module_add(request: HttpRequest, pk: int) -> HttpResponse:
    """Derive new module ownership from a selector-filtered course."""
    course = get_object_or_404(selectors.managed_courses(request.user), pk=pk)
    action = FormAction(
        ModuleForm,
        partial(services.add_module, request.user, course),
        success_url=reverse("courses:detail", args=[pk]),
        title="Add module",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def module_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Keep another trainer's stations indistinguishable from missing IDs."""
    module = get_object_or_404(selectors.managed_modules(request.user), pk=pk)
    action = FormAction(
        ModuleForm,
        partial(services.update_module, request.user, module),
        module,
        reverse("courses:detail", args=[module.course_id]),
        "Edit module",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def module_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Preserve progress errors as feedback without allowing destructive GETs."""
    module = get_object_or_404(selectors.managed_modules(request.user), pk=pk)
    return action_response(
        request,
        partial(services.delete_module, request.user, module),
        reverse("courses:detail", args=[module.course_id]),
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_safe
def course_participants(request: HttpRequest, pk: int) -> HttpResponse:
    """Protect participation counts with the same course ownership filter."""
    course = get_object_or_404(selectors.managed_courses(request.user), pk=pk)
    return render(
        request,
        "courses/participants.html",
        {
            "course": course,
            "enrollments": selectors.course_participants(request.user, course),
        },
    )
