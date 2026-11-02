"""Provide hashed fixed-window cache counters without account-only lockouts."""

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from math import ceil

from django.core.cache import cache

from apps.core import clock

NAMESPACE = "capacity-connect:throttle"


@dataclass(frozen=True, slots=True)
class Policy:
    """Bind each counter's namespace, request limit and window duration."""

    name: str
    limit: int
    window: int


@dataclass(frozen=True, slots=True)
class Decision:
    """Return a bounded retry hint without exposing raw cache identities."""

    allowed: bool
    retry_after: int


def counter_key(policy: Policy, identity: tuple) -> tuple[str, int]:
    """Hash every identity component and partition windows using the shared clock."""
    stamp = clock.now().timestamp()
    bucket = int(stamp // policy.window)
    remaining = ceil(policy.window - stamp % policy.window)
    digest = sha256(
        dumps(identity, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    return f"{NAMESPACE}:{policy.name}:{bucket}:{digest}", remaining


def _increment(key: str, timeout: int) -> int:
    """Use add/incr while tolerating eviction between the two cache operations."""
    if cache.add(key, 1, timeout):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.add(key, 1, timeout)
        return cache.get(key, 1)


def check(policy: Policy, identity: tuple, consume: bool = True) -> Decision:
    """Allow up to the limit and expose only the current fixed-window retry delay."""
    key, remaining = counter_key(policy, identity)
    count = _increment(key, remaining) if consume else cache.get(key, 0)
    return Decision(
        count <= policy.limit if consume else count < policy.limit, remaining
    )


def reset(policy: Policy, identity: tuple) -> None:
    """Reset only the caller-selected current-window counter after successful login."""
    key, _ = counter_key(policy, identity)
    cache.delete(key)
