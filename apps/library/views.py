"""Keep resource controllers thin, role-explicit and selector-filtered."""

from functools import partial
from pathlib import PurePath

from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.core.form_views import FormAction, action_response, form_response
from apps.library import selectors, services
from apps.library.constants import CONTENT_TYPES, LIBRARY_PAGE_SIZE, ResourceKind
from apps.library.forms import ResourceFilterForm, ResourceForm


@role_required(*UserRole.values)
@require_safe
def resource_list(request: HttpRequest) -> HttpResponse:
    """Validate filters before paginating visibility-filtered resources."""
    form = ResourceFilterForm(request.GET)
    resources = (
        selectors.visible_resources(request.user, **form.cleaned_data)
        if form.is_valid()
        else selectors.visible_resources(request.user).none()
    )
    page = Paginator(resources, LIBRARY_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "library/list.html", {"page_obj": page, "filter_form": form})


@role_required(*UserRole.values)
@require_safe
def resource_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Return 404 before exposing metadata from an unpublished private resource."""
    resource = get_object_or_404(selectors.visible_resources(request.user), pk=pk)
    return render(
        request, "library/detail.html", selectors.detail_context(request.user, resource)
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def resource_create(request: HttpRequest) -> HttpResponse:
    """Keep resource ownership under server-side role control."""
    action = FormAction(
        partial(ResourceForm, actor=request.user),
        partial(services.create_resource, request.user),
        success_url=reverse("library:list"),
        title="Create resource",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def resource_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Resolve persisted resource ownership before accepting replacements."""
    resource = get_object_or_404(selectors.managed_resources(request.user), pk=pk)
    action = FormAction(
        partial(ResourceForm, actor=request.user),
        partial(services.update_resource, request.user, resource),
        resource,
        reverse("library:detail", args=[pk]),
        "Edit resource",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def resource_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete managed evidence only through an explicit POST action."""
    resource = get_object_or_404(selectors.managed_resources(request.user), pk=pk)
    return action_response(
        request,
        partial(services.delete_resource, request.user, resource),
        reverse("library:list"),
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def resource_publish(request: HttpRequest, pk: int) -> HttpResponse:
    """Expose resource publication through the domain service."""
    resource = get_object_or_404(selectors.managed_resources(request.user), pk=pk)
    return action_response(
        request,
        partial(services.publish, request.user, resource),
        reverse("library:detail", args=[pk]),
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def resource_unpublish(request: HttpRequest, pk: int) -> HttpResponse:
    """Withdraw public visibility without removing retained private evidence."""
    resource = get_object_or_404(selectors.managed_resources(request.user), pk=pk)
    return action_response(
        request,
        partial(services.unpublish, request.user, resource),
        reverse("library:detail", args=[pk]),
    )


@role_required(*UserRole.values)
@require_safe
def download(request: HttpRequest, pk: int) -> FileResponse:
    """Authorize visibility before streaming private video or documents."""
    resource = get_object_or_404(selectors.visible_resources(request.user), pk=pk)
    try:
        stream = resource.file.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    response = FileResponse(
        stream,
        as_attachment=resource.kind != ResourceKind.VIDEO,
        filename=PurePath(resource.file.name).name,
        content_type=CONTENT_TYPES[PurePath(resource.file.name).suffix.lower()],
    )
    response["Cache-Control"] = "private, no-store"
    return response
