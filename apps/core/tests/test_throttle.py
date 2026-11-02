"""Pin cache windows, identity boundaries and non-enumerating failure limits."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import MOMENT
from apps.core import clock
from apps.core.client_ip import client_ip
from apps.core.throttle import Policy, check, counter_key


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch: object) -> None:
    """Exercise fixed-window boundaries without sleeping."""
    monkeypatch.setattr(clock, "now", lambda: MOMENT)


def test_fixed_window_threshold_and_rollover(monkeypatch: object) -> None:
    """Permit the configured count, then recover at the exact next window."""
    policy = Policy("test", 2, 60)
    assert check(policy, ("identity",)).allowed
    assert check(policy, ("identity",)).allowed
    blocked = check(policy, ("identity",))
    assert not blocked.allowed and blocked.retry_after == 60
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(seconds=60))
    assert check(policy, ("identity",)).allowed


def test_cache_keys_hash_every_identity_and_handle_eviction() -> None:
    """Keep usernames/IPs out of key names and tolerate an add/incr eviction race."""
    policy = Policy("test", 1, 60)
    key, _ = counter_key(policy, ("192.0.2.1", "victim@example.com"))
    assert "192.0.2.1" not in key and "victim" not in key
    with (
        patch("apps.core.throttle.cache.add", side_effect=[False, True]),
        patch("apps.core.throttle.cache.incr", side_effect=ValueError),
        patch("apps.core.throttle.cache.get", return_value=1),
    ):
        assert check(policy, ("evicted",)).allowed


@pytest.mark.parametrize(
    "count,header,expected",
    [
        (0, "198.51.100.1", "127.0.0.1"),
        (1, "198.51.100.1, 192.0.2.2", "192.0.2.2"),
        (2, "198.51.100.1, 192.0.2.2", "198.51.100.1"),
        (3, "198.51.100.1", "127.0.0.1"),
        (1, "invalid", "127.0.0.1"),
    ],
)
def test_forwarded_ip_is_ignored_unless_explicitly_trusted(
    count: int, header: str, expected: str, settings: object
) -> None:
    """Use only REMOTE_ADDR by default and validated trusted-chain entries otherwise."""
    settings.TRUSTED_PROXY_COUNT = count
    request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR=header)
    assert client_ip(request) == expected


@pytest.mark.django_db
def test_login_pair_limit_different_name_and_ip_remain_independent(
    client: object, settings: object
) -> None:
    """Never let one username or spoofed header lock a victim out on another IP."""
    settings.LOGIN_FAILURE_LIMIT = 2
    for _ in range(2):
        assert login_post(client, "Victim", REMOTE_ADDR="192.0.2.1").status_code == 200
    assert (
        login_post(
            client,
            "victim",
            REMOTE_ADDR="192.0.2.1",
            HTTP_X_FORWARDED_FOR="198.51.100.9",
        ).status_code
        == 429
    )
    assert login_post(client, "other", REMOTE_ADDR="192.0.2.1").status_code == 200
    assert login_post(client, "victim", REMOTE_ADDR="192.0.2.2").status_code == 200


@pytest.mark.django_db
def test_login_ip_limit_spans_usernames(client: object, settings: object) -> None:
    """Limit failure spraying across names without using a username-only counter."""
    settings.LOGIN_IP_LIMIT = 2
    for name in ("first", "second"):
        assert login_post(client, name, "wrong").status_code == 200
    response = login_post(client, "third", "wrong")
    assert response.status_code == 429 and response["Retry-After"] == "900"


@pytest.mark.django_db
def test_success_resets_pair_but_not_ip_counter(
    client: object, settings: object
) -> None:
    """Keep shared-IP failure history after a successful eligible login."""
    settings.LOGIN_FAILURE_LIMIT = 2
    settings.LOGIN_IP_LIMIT = 3
    user = UserFactory(approved_trainee=True)
    assert login_post(client, user.username, "wrong").status_code == 200
    assert login_post(client, user.username, "TestPassword123!").status_code == 302
    client.post(reverse("logout"))
    for _ in range(2):
        assert login_post(client, user.username, "wrong").status_code == 200
    assert login_post(client, "new-name", "wrong").status_code == 429


@pytest.mark.django_db
def test_unknown_and_existing_users_have_identical_429_and_safe_log(
    client: object, settings: object, caplog: object
) -> None:
    """Keep throttling independent of account existence and never log the password."""
    settings.LOGIN_FAILURE_LIMIT = 1
    user = UserFactory(approved_trainee=True)
    responses = []
    for name in (user.username, "unknown-person"):
        login_post(client, name, "never-log-this-password")
        responses.append(login_post(client, name, "never-log-this-password"))
    assert all(r.status_code == 429 for r in responses)
    assert (
        responses[0].content == responses[1].content
        and responses[0]["Retry-After"] == responses[1]["Retry-After"]
    )
    assert (
        "request_throttled" in caplog.text
        and "never-log-this-password" not in caplog.text
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,limit_name",
    [("signup", "SIGNUP_IP_LIMIT"), ("certificates:verify_form", "VERIFY_IP_LIMIT")],
)
def test_signup_and_verify_handler_limits(
    client: object, settings: object, name: str, limit_name: str
) -> None:
    """Count public handler requests and supply a retry hint when over the limit."""
    setattr(settings, limit_name, 2)
    url = reverse(name)
    assert client.get(url).status_code == client.get(url).status_code == 200
    response = client.get(url)
    assert response.status_code == 429 and int(response["Retry-After"]) > 0


@pytest.mark.django_db
def test_django_admin_login_uses_the_same_failure_limit(
    client: object, settings: object
) -> None:
    """Close the alternate staff-login brute-force surface too."""
    settings.LOGIN_FAILURE_LIMIT = 1
    url = reverse("admin:login")
    assert (
        client.post(url, {"username": "unknown-staff", "password": "wrong"}).status_code
        == 200
    )
    assert (
        client.post(url, {"username": "unknown-staff", "password": "wrong"}).status_code
        == 429
    )


def login_post(
    client: object, name: str, password: str = "wrong", **kwargs: object
) -> object:
    """Share request shape while tests vary only identity and source IP."""
    return client.post(
        reverse("login"), {"username": name, "password": password}, **kwargs
    )
