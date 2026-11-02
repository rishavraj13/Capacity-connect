"""Share rate-limit enforcement at public form/view boundaries."""

import logging
from collections.abc import Callable
from enum import StrEnum
from functools import wraps
from hashlib import sha256

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.core.client_ip import client_ip
from apps.core.throttle import Policy, check, reset

logger = logging.getLogger("security.throttle")


class Kind(StrEnum):
    """Keep public limiter scopes independent of URL paths and user existence."""

    LOGIN = "login"
    SIGNUP = "signup"
    VERIFY = "verify"


def login_policies(request: HttpRequest) -> tuple:
    """Scope failures by IP/name pair plus IP, never by username alone."""
    ip = client_ip(request)
    username = request.POST.get("username", "").strip().lower()
    return (
        (
            Policy(
                "login-pair",
                settings.LOGIN_FAILURE_LIMIT,
                settings.LOGIN_WINDOW_SECONDS,
            ),
            (ip, username),
        ),
        (
            Policy("login-ip", settings.LOGIN_IP_LIMIT, settings.LOGIN_WINDOW_SECONDS),
            (ip,),
        ),
    )


def request_policies(request: HttpRequest, kind: Kind) -> tuple:
    """Count only login failures but every signup/verification handler request."""
    if kind == Kind.LOGIN:
        return login_policies(request) if request.method == "POST" else ()
    limit, window = (
        (settings.SIGNUP_IP_LIMIT, settings.SIGNUP_WINDOW_SECONDS)
        if kind == Kind.SIGNUP
        else (settings.VERIFY_IP_LIMIT, settings.VERIFY_WINDOW_SECONDS)
    )
    return ((Policy(kind, limit, window), (client_ip(request),)),)


def _blocked(request: HttpRequest, kind: Kind, retry: int) -> HttpResponse:
    """Keep response shape and logs independent of account existence or passwords."""
    digest = sha256(client_ip(request).encode()).hexdigest()
    logger.warning(
        "request_throttled kind=%s ip_hash=%s retry_after=%s", kind, digest, retry
    )
    response = render(request, "429.html", status=429)
    response["Retry-After"] = str(retry)
    return response


def enforce(request: HttpRequest, kind: Kind) -> HttpResponse | None:
    """Use one shared preflight for login and consuming public request counters."""
    for policy, identity in request_policies(request, kind):
        decision = check(policy, identity, consume=kind != Kind.LOGIN)
        if not decision.allowed:
            return _blocked(request, kind, decision.retry_after)
    return None


def throttled(kind: Kind) -> Callable:
    """Apply the same cache-backed response coordinator without copying view logic."""

    def decorate(view: Callable) -> Callable:
        """Retain route metadata for the security audit."""

        @wraps(view)
        def wrapped(
            request: HttpRequest, *args: object, **kwargs: object
        ) -> HttpResponse:
            """Short-circuit only blocked requests before a form handler runs."""
            response = enforce(request, kind)
            return response if response is not None else view(request, *args, **kwargs)

        return wrapped

    return decorate


def record_login_failure(request: HttpRequest) -> None:
    """Count failed validation only after the existing login form rejects input."""
    for policy, identity in login_policies(request):
        check(policy, identity)


def reset_login_pair(request: HttpRequest) -> None:
    """Leave shared-IP failure history intact when a pair successfully logs in."""
    policy, identity = login_policies(request)[0]
    reset(policy, identity)
