"""Pin reviewer-requested demo completeness and production credential safety."""

from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.test import RequestFactory

from apps.assessments.tests.factories import MOMENT
from apps.core import clock
from apps.core.client_ip import client_ip
from apps.profiles.models import ExternalCertificate, Qualification, WorkExperience


@pytest.mark.parametrize("trusted,expected", [(0, "192.0.2.10"), (1, "198.51.100.9")])
def test_proxy_uses_rightmost_client_and_ignores_forged_left_entry(
    settings: object, trusted: int, expected: str
) -> None:
    """Keep a forged extra left entry outside the trusted one-proxy boundary."""
    settings.TRUSTED_PROXY_COUNT = trusted
    request = RequestFactory().get(
        "/",
        REMOTE_ADDR="192.0.2.10",
        HTTP_X_FORWARDED_FOR="203.0.113.66, 198.51.100.9",
    )
    assert client_ip(request) == expected


@pytest.mark.django_db
def test_demo_has_professional_history_and_external_evidence(settings: object) -> None:
    """Exercise real child services across approved trainee profiles."""
    settings.DEBUG = True
    with clock.at(MOMENT):
        call_command("seed_demo_data", stdout=StringIO())
    assert Qualification.objects.count() == WorkExperience.objects.count() == 3
    assert ExternalCertificate.objects.count() == 2
    for record in ExternalCertificate.objects.select_related("profile__user"):
        assert record.profile.user.is_approved and record.file.size > 0


@pytest.mark.django_db
def test_forced_non_debug_seed_requires_explicit_password(
    settings: object, monkeypatch: object
) -> None:
    """Prevent --force from silently using the public development password."""
    settings.DEBUG = False
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    with pytest.raises(CommandError, match="DEMO_PASSWORD"):
        call_command("seed_demo_data", force=True, stdout=StringIO())
    monkeypatch.setenv("DEMO_PASSWORD", "Explicit-Seed-2026!")
    settings.DEMO_PASSWORD = "Explicit-Seed-2026!"
    with clock.at(MOMENT):
        call_command("seed_demo_data", force=True, stdout=StringIO())
