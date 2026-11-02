"""Keep successful authentication response coordination out of the form handler."""

from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from apps.accounts.constants import ROLE_HOME_URL_NAMES
from apps.core.rate_views import reset_login_pair


def login_response(request: HttpRequest, user: object) -> HttpResponse:
    """Reset only the successful IP/name pair and preserve safe next redirects."""
    reset_login_pair(request)
    login(request, user)
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect(ROLE_HOME_URL_NAMES.get(user.role, "login"))
