"""Prove every route is public explicitly or refuses anonymous access."""

import pytest
from django.http import HttpResponse

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.route_audit import (
    PUBLIC_NAMES,
    STATE_NAMES,
    Route,
    assert_declared,
    routes,
)


@pytest.mark.django_db
@pytest.mark.parametrize("route", routes(), ids=lambda route: route.name)
def test_every_route_declares_access_and_denies_anonymous_unless_public(
    client: object, route: Route
) -> None:
    """Audit callback metadata and actual anonymous behavior for every URL pattern."""
    assert_declared(route)
    response = client.get(route.url)
    if route.name not in PUBLIC_NAMES:
        assert response.status_code in {302, 403, 404, 405}, route.name
    if response.streaming:
        response.close()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "route",
    [r for r in routes() if r.name in STATE_NAMES],
    ids=lambda route: route.name,
)
def test_every_state_action_returns_405_on_get(client: object, route: Route) -> None:
    """Use the allowed role so the method guard runs before dummy-object lookup."""
    roles = getattr(route.callback, "allowed_roles", ())
    role = roles[0] if roles else "ADMIN"
    user = UserFactory(
        role=role, is_active=True, is_approved=True, is_staff=role == "ADMIN"
    )
    client.force_login(user)
    assert client.get(route.url).status_code == 405, route.name


def test_audit_rejects_new_route_without_role_check() -> None:
    """Demonstrate that an unguarded callback cannot pass by returning a dummy 404."""

    def accidental(request: object) -> HttpResponse:
        """Represent a future developer forgetting a private route's role decorator."""
        return HttpResponse(status=404)

    with pytest.raises(AssertionError):
        assert_declared(Route("future-private", "/future/", accidental, False))


def test_route_names_are_unique_for_reliable_auditing() -> None:
    """Prevent a duplicate public name from masking a different private callback."""
    names = [route.name for route in routes()]
    assert len(names) == len(set(names))
