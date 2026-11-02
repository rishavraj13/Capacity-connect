"""Exercise explicit shared reads and forbidden cross-owner HTTP requests."""

import json
from pathlib import Path

from django.apps import apps

from apps.core.tests.journeys.isolation_routes import (
    BINDINGS,
    SELF_ACTIONS,
    SHARED_READS,
    identifier_routes,
    methods_for,
    target_url,
)
from apps.courses.models import Enrollment


def persisted_state() -> dict:
    """Prove denied writes leave domain rows untouched, excluding sessions."""
    return {
        model._meta.label: list(model.objects.order_by("pk").values())
        for model in apps.get_models(include_auto_created=True)
        if model._meta.app_label not in {"sessions"}
    }


def walk_foreign_routes(actor: tuple, target: dict) -> list:
    """Fail on unclassified new routes while testing real target IDs through HTTP."""
    inventory = identifier_routes()
    assert set(inventory) == set(BINDINGS)
    before, evidence = persisted_state(), []
    for route, shared in _foreign_cases(inventory, target):
        _check_request(actor[0], route, shared, evidence)
    assert persisted_state() == before
    _self_actions(actor, target, evidence)
    return evidence


def _foreign_cases(inventory: dict, target: dict) -> object:
    """Enumerate every target variant without changing another user's state."""
    for name, keys in inventory.items():
        if name in SELF_ACTIONS:
            continue
        kinds = (
            ("trainee", "trainer", "certificate")
            if name == "profiles:private_file"
            else ("trainee",)
        )
        for kind in kinds:
            url = target_url(name, keys, target, kind)
            shared = name in SHARED_READS or (
                name == "profiles:private_file" and kind == "trainer"
            )
            yield (name, url, kind), shared


def _check_request(client: object, route: tuple, shared: bool, evidence: list) -> None:
    """Check denied/shared content and save the exact route/method result."""
    name, url, kind = route
    for method in methods_for(name):
        response = getattr(client, method)(url)
        allowed = {200} if shared else {403, 404}
        assert response.status_code in allowed, (
            name,
            kind,
            method,
            response.status_code,
        )
        _assert_content(response, shared)
        evidence.append(
            (
                name,
                kind,
                method,
                response.status_code,
                "shared" if shared else "restricted",
            )
        )


def _assert_content(response: object, shared: bool) -> None:
    """Verify visible states and close private file streams after reading bytes."""
    if response.streaming:
        assert response["Content-Disposition"].startswith("attachment;")
        assert b"".join(response.streaming_content)
        response.close()
    elif shared:
        assert any(
            word in response.content
            for word in (b"Journey course", b"Private workbook", b"Experience:")
        )
    else:
        assert b"Forbidden" in response.content or b"Not found" in response.content


def _self_actions(actor: tuple, target: dict, evidence: list) -> None:
    """Keep legitimate self participation separate from cross-owner mutation checks."""
    client, role = actor
    inventory = identifier_routes()
    for name in sorted(SELF_ACTIONS):
        url = target_url(name, inventory[name], target)
        method = "post" if name == "courses:enroll" else "get"
        response = getattr(client, method)(url)
        expected = (302 if method == "post" else 200) if role == "learner" else 403
        assert response.status_code == expected, (name, role, response.status_code)
        _assert_self_result(client, (name, role), target, response)
        evidence.append(
            (name, "self", method, response.status_code, "self participation")
        )
    target["enrollment"].refresh_from_db()
    assert target["enrollment"].status == "COMPLETED"


def _assert_self_result(
    client: object, case: tuple, target: dict, response: object
) -> None:
    """Keep enrollment writes on a new own row and preserve the target's history."""
    name, role = case
    if role == "learner" and name == "courses:enroll":
        own = Enrollment.objects.get(
            course=target["course"], trainee_id=client.session["_auth_user_id"]
        )
        assert own.pk != target["enrollment"].pk and own.status == "ACTIVE"
    if response.status_code == 200:
        assert b"Rating" in response.content


def record_walk(key: str, evidence: list) -> None:
    """Keep route/method evidence local rather than commit root transcripts."""
    path = Path(__file__).resolve().parents[4] / ".local/reports/T1_J3_HTTP.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    rows[key] = evidence
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
