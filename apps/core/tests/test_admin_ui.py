"""Check rendered Control room, account actions and role navigation."""

import re

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.test_trainee_learning import learning_html
from apps.courses.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db

ADMIN_NAV_ROUTES = (
    "admin_panel",
    "admin_user_list",
    "admin_pending_list",
    "catalog:subject_list",
    "announcements:manage",
    "competency:ranking",
    "courses:list",
    "library:list",
)


@pytest.fixture
def administrator(client: object) -> object:
    """Use the existing staff and portal permissions in the same session."""
    user = UserFactory(active_admin=True)
    client.force_login(user)
    return user


def test_control_room_zero_and_populated_line_load(
    client: object, administrator: object
) -> None:
    """Use existing dashboard aggregates, explicit zeros and bounded meter ranges."""
    assert "Control room" in learning_html(client, "admin_panel")
    zero = learning_html(client, "dashboards:admin")
    assert zero.count("0.00%") == 3
    assert "No submitted attempts yet." in zero
    assert "No active subjects yet." in zero
    enrollment = EnrollmentFactory()
    EnrollmentFactory(course=enrollment.course)
    UserFactory(pending_trainer=True)
    full = learning_html(client, "dashboards:admin")
    assert "<caption>Subject enrollment and active line load</caption>" in full
    assert 'max="2" value="2"' in full
    assert "Review pending approvals" in full
    assert client.get(reverse("admin:index")).status_code == 200


@pytest.mark.usefixtures("administrator")
@pytest.mark.parametrize(
    ("status", "trait", "badge"),
    (
        ("active", "approved_trainee", "Approved"),
        ("pending", "pending_trainee", "Pending"),
        ("inactive", "rejected_user", "Inactive"),
    ),
)
def test_admin_user_status_filters(
    client: object, status: str, trait: str, badge: str
) -> None:
    """Preserve existing filters and show each account state in text."""
    row = UserFactory(first_name="DisplayName", **{trait: True})
    other = UserFactory(approved_trainer=True)
    response = client.get(
        reverse("admin_user_list"), {"role": "TRAINEE", "status": status}
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert row.username in html and "DisplayName" in html and f">{badge}<" in html
    assert other.username not in html
    assert 'scope="row"' in html and "<caption>" in html


def test_approval_actions_have_native_confirmation_and_post_boundary(
    client: object, administrator: object
) -> None:
    """Keep the action endpoints and return destinations on their original pages."""
    empty = learning_html(client, "admin_pending_list")
    assert "No applications currently awaiting" in empty
    row = UserFactory(pending_trainer=True)
    pending = learning_html(client, "admin_pending_list")
    assert row.username in pending and ">Pending<" in pending
    assert (
        "<summary>Reject / Disable</summary>" in pending and "Confirm reject" in pending
    )
    users = learning_html(client, "admin_user_list")
    assert f'for="change-role-{row.pk}"' in users
    for name, html in (
        ("admin_approve_user", pending),
        ("admin_reject_user", pending),
        ("admin_change_role", users),
    ):
        _assert_post_control(client, html, name, row.pk)


def _assert_post_control(client: object, html: str, name: str, pk: int) -> None:
    """Verify the rendered method, CSRF token and rejection of a safe request."""
    url = reverse(name, args=[pk])
    form = re.search(
        r'<form method="post" action="' + re.escape(url) + r'"[^>]*>(.*?)</form>',
        html,
        re.S,
    )
    assert form and 'name="csrfmiddlewaretoken"' in form[1]
    assert client.get(url).status_code == 405


@pytest.mark.parametrize("role", ("anonymous", "trainee", "trainer", "admin"))
def test_main_nav_lists_only_openable_routes_for_each_role(
    client: object, role: str
) -> None:
    """Walk rendered links and verify distinct role destinations and Admin order."""
    traits = {
        "trainee": "approved_trainee",
        "trainer": "approved_trainer",
        "admin": "active_admin",
    }
    if role in traits:
        client.force_login(UserFactory(**{traits[role]: True}))
    html = learning_html(client, "announcements:home")
    nav = html.split('<nav aria-label="Main Navigation"', 1)[1].split("</nav>", 1)[0]
    urls = re.findall(r'href="([^"]+)"', nav)
    if role == "admin":
        assert urls[:8] == [reverse(name) for name in ADMIN_NAV_ROUTES]
    else:
        assert reverse("admin_panel") not in urls
    assert (reverse("assessments:mine") in urls) == (role == "trainee")
    assert (reverse("competency:mine") in urls) == (role == "trainer")
    assert all(client.get(url).status_code == 200 for url in urls)
