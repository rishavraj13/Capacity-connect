"""Inventory actual URL patterns so unknown unguarded routes cannot hide behind 404s."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from django.contrib.admin import AdminSite
from django.urls import URLResolver, get_resolver, reverse

PUBLIC_NAMES = frozenset(
    {
        "announcements:home",
        "login",
        "signup",
        "certificates:verify",
        "certificates:verify_form",
        "admin:login",
    }
)
STATE_NAMES = frozenset(
    {
        "logout",
        "admin_approve_user",
        "admin_reject_user",
        "admin_change_role",
        "catalog:subject_deactivate",
        "catalog:subject_reactivate",
        "catalog:skill_delete",
        "profiles:qualification_delete",
        "profiles:experience_delete",
        "profiles:certificate_delete",
        "courses:publish",
        "courses:unpublish",
        "courses:module_delete",
        "courses:enroll",
        "courses:drop",
        "courses:complete_module",
        "library:delete",
        "assessments:delete",
        "assessments:question_delete",
        "assessments:start",
        "feedback:delete",
        "competency:remove",
        "announcements:publish",
        "announcements:unpublish",
        "announcements:delete",
    }
)


@dataclass(frozen=True, slots=True)
class Route:
    """Carry callback metadata alongside a real reversible audit URL."""

    name: str
    url: str
    callback: Callable
    admin: bool


def _sample(name: str) -> str | int:
    """Use valid converter samples without requiring persisted target records."""
    values = {
        "app_label": "accounts",
        "model_name": "user",
        "identifier": "CC-2026-00001",
        "kind": "photo",
        "url": "not-found",
    }
    return values.get(name, 1)


def routes(
    patterns: object = None, namespaces: tuple = (), prefix: str = ""
) -> tuple[Route, ...]:
    """Walk nested includes, including every built-in admin pattern."""
    result = []
    for pattern in patterns if patterns is not None else get_resolver().url_patterns:
        if isinstance(pattern, URLResolver):
            result.extend(
                routes(
                    pattern.url_patterns,
                    namespaces + ((pattern.namespace,) if pattern.namespace else ()),
                    prefix + str(pattern.pattern),
                )
            )
        else:
            result.append(_route(pattern, namespaces, prefix))
    return tuple(result)


def _route(pattern: object, namespaces: tuple, prefix: str) -> Route:
    """Reverse named routes and explicitly sample Django's unnamed admin catch-all."""
    name = ":".join((*namespaces, pattern.name or "UNNAMED"))
    kwargs = {key: _sample(key) for key in pattern.pattern.regex.groupindex}
    if pattern.name:
        url = reverse(name, kwargs=kwargs)
    else:
        suffix = re.sub(
            r"\(\?P<(\w+)>[^)]+\)",
            lambda match: str(_sample(match.group(1))),
            pattern.pattern.regex.pattern,
        )
        url = "/" + prefix + suffix.replace("\\Z", "").strip("^$")
        name = ":".join((*namespaces, "redirect", url))
    return Route(name, url, pattern.callback, "admin" in namespaces)


def assert_declared(route: Route) -> None:
    """Require public names or role guards, retaining POST-only logout."""
    if route.name in PUBLIC_NAMES or route.name == "logout":
        return
    if route.admin:
        assert _admin_guarded(route.callback), route.name
        return
    roles = getattr(route.callback, "allowed_roles", ())
    view_class = getattr(route.callback, "view_class", None)
    assert roles or (view_class and getattr(view_class, "allowed_roles", ())), (
        route.name
    )


def _admin_guarded(callback: Callable) -> bool:
    """Recognize Django's admin_view closure as well as its standard metadata."""
    pending = [callback]
    seen = set()
    while pending:
        candidate = pending.pop()
        if id(candidate) in seen:
            continue
        seen.add(id(candidate))
        if getattr(candidate, "admin_site", None) or getattr(
            candidate, "model_admin", None
        ):
            return True
        for cell in getattr(candidate, "__closure__", None) or ():
            value = cell.cell_contents
            if isinstance(value, AdminSite):
                return True
            if callable(value):
                pending.append(value)
    return False
