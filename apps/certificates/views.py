"""Deliver protected PDFs and minimal public certificate verification."""

from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.certificates import selectors
from apps.certificates.forms import VerificationForm
from apps.core.rate_views import Kind, throttled


@role_required(UserRole.TRAINEE)
@require_safe
def mine(request: HttpRequest) -> HttpResponse:
    """List only the trainee's own durable certificate records."""
    return render(
        request,
        "certificates/mine.html",
        {"certificates": selectors.certificates_for_trainee(request.user)},
    )


@role_required(*UserRole.values)
@require_safe
def download(request: HttpRequest, pk: int) -> HttpResponse:
    """Authorize before opening private storage and force attachment delivery."""
    row = get_object_or_404(selectors.visible_certificates(request.user), pk=pk)
    response = FileResponse(
        row.pdf.open("rb"),
        as_attachment=True,
        filename=f"{row.certificate_id}.pdf",
        content_type="application/pdf",
    )
    response["Cache-Control"] = "private, no-store"
    return response


def _verification_headers(response: HttpResponse) -> HttpResponse:
    """Discourage indexing and referrer leakage on every verification response."""
    response["X-Robots-Tag"] = "noindex"
    response["Referrer-Policy"] = "no-referrer"
    return response


@require_safe
@throttled(Kind.VERIFY)
def verify_form(request: HttpRequest) -> HttpResponse:
    """Allow public GET lookup without disclosing private certificate metadata."""
    form = VerificationForm(request.GET or None)
    if form.is_bound and form.is_valid():
        return _verification_headers(
            redirect(
                "certificates:verify", identifier=form.cleaned_data["certificate_id"]
            )
        )
    return _verification_headers(
        render(request, "certificates/verify_form.html", {"form": form})
    )


@require_safe
@throttled(Kind.VERIFY)
def verify(request: HttpRequest, identifier: str) -> HttpResponse:
    """Use the same public 404 body for unknown and malformed identifiers."""
    record = selectors.public_verification(identifier)
    template = "certificates/verify.html" if record else "certificates/not_found.html"
    return _verification_headers(
        render(request, template, {"record": record}, status=200 if record else 404)
    )
