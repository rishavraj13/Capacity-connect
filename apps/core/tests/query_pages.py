"""Compare real rendered pages at two sizes after a framework-cache warmup."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from django.db import connection
from django.test.utils import CaptureQueriesContext


@dataclass(frozen=True, slots=True)
class PageSetup:
    """Group an actor, URL and dataset expansion without sharing row-specific SQL."""

    url: str
    user: object
    expand: Callable


def _queries(client: object, url: str) -> int:
    """Count the complete authenticated template response, not just a selector."""
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        if response.streaming:
            response.close()
    return len(queries)


def assert_stable_page(client: object, name: str, setup: PageSetup) -> tuple[int, int]:
    """Warm framework metadata once, then compare SMALL/LARGE rendered responses."""
    if setup.user:
        client.force_login(setup.user)
    _queries(client, setup.url)
    small = _queries(client, setup.url)
    setup.expand()
    large = _queries(client, setup.url)
    record_counts(name, small, large)
    assert small == large, f"{name}: SMALL={small}, LARGE={large}"
    return small, large


def record_counts(name: str, small: int, large: int) -> None:
    """Keep exact gate evidence ignored instead of adding root transcripts."""
    path = Path(__file__).resolve().parents[3] / ".local/reports/B7_PAGE_QUERIES.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data[name] = {"small": small, "large": large}
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
