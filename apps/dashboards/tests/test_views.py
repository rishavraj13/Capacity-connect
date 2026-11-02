"""Keep trainer data isolated and role landing URL names unchanged."""

import pytest
from django.urls import reverse

from apps.dashboards.tests.factories import analytics_dataset

pytestmark = pytest.mark.django_db


def test_trainer_dashboard_never_shows_other_trainers_course(client: object) -> None:
    """Use the session owner rather than accepting a forged trainer query parameter."""
    data = analytics_dataset()
    client.force_login(data["trainer"])
    response = client.get(reverse("dashboards:trainer"), {"trainer": data["other"].pk})
    assert response.status_code == 200 and b"Published own" in response.content
    assert b"Other trainer course" not in response.content
    assert (
        reverse("assessments:participation", args=[data["quizzes"][0].pk]).encode()
        in response.content
    )


def test_landing_pages_link_to_new_flows_without_renaming_urls(client: object) -> None:
    """Keep existing landing routes while exposing the new read-only pages."""
    data = analytics_dataset()
    client.force_login(data["trainer"])
    assert reverse("trainer_home") == "/trainer/"
    assert b"/dashboards/trainer/" in client.get(reverse("trainer_home")).content
    client.force_login(data["admin"])
    assert reverse("admin_panel") == "/admin-panel/"
    assert b"/dashboards/admin/" in client.get(reverse("admin_panel")).content
    assert reverse("trainee_home") == "/trainee/"
