"""Add a single configured CSP without coupling error pages to application data."""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    """Keep CSP policy in settings so the approved frontend can adjust it later."""

    def __init__(self, get_response: Callable) -> None:
        """Store Django's response continuation without startup queries."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Apply the same policy to public, authenticated and error responses."""
        response = self.get_response(request)
        response["Content-Security-Policy"] = settings.CONTENT_SECURITY_POLICY
        return response
