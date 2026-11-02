"""Verify deterministic service-driven demo data and a no-write second run."""

import json
from io import StringIO
from pathlib import Path

import pytest
from django.apps import apps
from django.core.management import CommandError, call_command
from django.db.models import Count

from apps.accounts.models import User
from apps.assessments.models import Attempt
from apps.assessments.tests.factories import MOMENT
from apps.certificates.models import Certificate
from apps.core import clock
from apps.core.demo_accounts import demo_accounts
from apps.core.demo_services import seed_demo_data
from apps.courses.selectors import station_map_for

pytestmark = pytest.mark.django_db


def snapshot() -> dict:
    """Compare actual stored values, including timestamps and file keys, on rerun."""
    return {
        model._meta.label: list(model.objects.order_by("pk").values())
        for model in apps.get_models(include_auto_created=True)
    }


def test_demo_seed_is_idempotent_with_all_requested_states(settings: object) -> None:
    """Exercise real domain workflows and preserve every row/file on a second run."""
    settings.DEBUG = True
    settings.DEMO_PASSWORD = "Demo-Connect-2026!"
    with clock.at(MOMENT):
        first = StringIO()
        call_command("seed_demo_data", stdout=first)
        before = snapshot()
        second = StringIO()
        call_command("seed_demo_data", stdout=second)
    assert snapshot() == before and first.getvalue() == second.getvalue()
    assert_seed_states()
    proof = {
        "first": {key: len(rows) for key, rows in before.items()},
        "second": {key: len(rows) for key, rows in snapshot().items()},
        "output": first.getvalue(),
    }
    path = Path(".local/reports/B7_SEED_PROOF.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proof, indent=2), encoding="utf-8")


def assert_seed_states() -> None:
    """Pin identity, outcome, interchange and all three station-map states."""
    assert (
        User.objects.count() == 16 and User.objects.filter(role="TRAINER").count() == 3
    )
    assert User.objects.filter(role="TRAINEE").count() == 12
    states = dict(Attempt.objects.values_list("status").annotate(number=Count("pk")))
    assert (
        states == {"SUBMITTED": 2, "TIMED_OUT": 1} and Certificate.objects.count() == 1
    )
    user = User.objects.get(username="demo_trainee_meera")
    stations = [station for line in station_map_for(user) for station in line.stations]
    assert {station.state for station in stations} == {"DONE", "CURRENT", "LOCKED"}
    assert any(station.is_interchange for station in stations)


def test_seed_requires_debug_and_explicit_production_force(
    settings: object, monkeypatch: object
) -> None:
    """Never create public demo credentials in production implicitly."""
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("seed_demo_data", stdout=StringIO())
    settings.DEBUG = True
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    with pytest.raises(CommandError):
        call_command("seed_demo_data", stdout=StringIO())
    with clock.at(MOMENT):
        assert seed_demo_data(force=True)["logins"]


def test_demo_account_builders_reuse_existing_namespace_accounts(
    settings: object,
) -> None:
    """Keep password/state intact when account construction is retried."""
    settings.DEMO_PASSWORD = "Demo-Connect-2026!"
    first = demo_accounts(settings.DEMO_PASSWORD)
    values = snapshot()
    second = demo_accounts(settings.DEMO_PASSWORD)
    assert second.admin.pk == first.admin.pk and snapshot() == values


def test_seed_command_help_and_validation_error(settings: object) -> None:
    """Expose the override in help and translate invalid demo passwords cleanly."""
    settings.DEBUG = True
    settings.DEMO_PASSWORD = "123"
    with pytest.raises(CommandError):
        call_command("seed_demo_data", stdout=StringIO())
