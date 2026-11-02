"""Serve private storage only after object visibility has been checked."""

from pathlib import PurePath

from django.http import FileResponse, Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.profiles import selectors

FILE_SELECTORS = {
    "trainee": (selectors.visible_trainees, "photo"),
    "trainer": (selectors.visible_trainers, "photo"),
    "certificate": (selectors.visible_certificates, "file"),
}
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}


@role_required(*UserRole.values)
@require_safe
def private_file(request: HttpRequest, kind: str, pk: int) -> FileResponse:
    """Apply profile visibility before opening an opaque storage key."""
    if kind not in FILE_SELECTORS:
        raise Http404
    selector, field = FILE_SELECTORS[kind]
    record = get_object_or_404(selector(request.user), pk=pk)
    file = getattr(record, field)
    if not file:
        raise Http404
    try:
        stream = file.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    response = FileResponse(
        stream,
        as_attachment=True,
        filename=PurePath(file.name).name,
        content_type=CONTENT_TYPES[PurePath(file.name).suffix.lower()],
    )
    response["Cache-Control"] = "private, no-store"
    return response
