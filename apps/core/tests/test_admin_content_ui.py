"""Exercise Admin catalog, announcements and ranking presentation."""

import pytest
from django.urls import reverse
from django.utils.text import Truncator

from apps.accounts.tests.factories import UserFactory
from apps.announcements.constants import BODY_MAX_LENGTH
from apps.announcements.tests.factories import AnnouncementFactory
from apps.catalog.tests.factories import SkillFactory, SubjectFactory
from apps.competency.tests.factories import CompetencyFactory
from apps.core.tests.frontend_markup import assert_accessible_shell
from apps.core.tests.test_admin_ui import _assert_post_control
from apps.core.tests.test_trainee_learning import learning_html

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def login_admin(client: object) -> None:
    """Exercise the real approved Admin routes."""
    client.force_login(UserFactory(active_admin=True))


def test_admin_catalog_status_and_protected_skill_confirmation(client: object) -> None:
    """Show both subject states and keep destructive controls explicit."""
    assert "No subjects yet." in learning_html(client, "catalog:subject_list")
    skill = SkillFactory()
    retired = SubjectFactory(is_active=False)
    html = learning_html(client, "catalog:subject_list")
    assert ">Active<" in html and ">Inactive<" in html and skill.name in html
    assert "<summary>Delete skill</summary>" in html and "Confirm delete" in html
    for name, pk in (
        ("catalog:subject_deactivate", skill.subject_id),
        ("catalog:subject_reactivate", retired.pk),
        ("catalog:skill_delete", skill.pk),
    ):
        _assert_post_control(client, html, name, pk)
    for name, args in (
        ("subject_create", ()),
        ("subject_edit", (retired.pk,)),
        ("skill_create", ()),
        ("skill_edit", (skill.pk,)),
    ):
        assert "Save" in learning_html(client, f"catalog:{name}", args)


def test_announcement_preview_matches_public_board_and_escapes(client: object) -> None:
    """Render the same truncated and escaped body in both authorized surfaces."""
    assert "No matching announcements." in learning_html(client, "announcements:manage")
    rows = [
        AnnouncementFactory(category=kind, published=True)
        for kind in ("NOTICE", "ACHIEVEMENT", "NEW_CONTENT", "DEADLINE")
    ]
    draft = AnnouncementFactory(title="Private draft example")
    row = rows[0]
    row.body = "<script>alert(1)</script>\n" + "Example " * 30
    row.save(update_fields=["body"])
    manage = learning_html(client, "announcements:manage")
    public = learning_html(client, "announcements:home")
    preview = "&lt;script&gt;alert(1)&lt;/script&gt;<br>"
    assert preview in manage and preview in public
    snippet = Truncator(row.body).chars(160).splitlines()[-1]
    assert snippet in manage and snippet in public
    assert all(
        f">{label}<" in manage for label in ("NOTICE", "ACHIEVED", "NEW", "DEADLINE")
    )
    assert draft.title in manage and draft.title not in public
    _assert_announcement_actions(client, manage, draft.pk, row.pk)


def _assert_announcement_actions(
    client: object, manage: str, draft: int, published: int
) -> None:
    """Check publish, withdrawal and delete method boundaries."""
    for name, pk in (("publish", draft), ("unpublish", published), ("delete", draft)):
        _assert_post_control(client, manage, f"announcements:{name}", pk)


def test_announcement_form_displays_live_limit_and_errors(client: object) -> None:
    """Expose the model limit and linked server errors on the existing forms."""
    row = AnnouncementFactory()
    for name, args in (("create", ()), ("edit", (row.pk,))):
        assert f"Maximum {BODY_MAX_LENGTH} characters." in learning_html(
            client, f"announcements:{name}", args
        )
    response = client.post(reverse("announcements:create"), {})
    assert response.status_code == 200
    html = response.content.decode()
    assert_accessible_shell(html)
    assert 'href="#id_body"' in html and "This field is required." in html


def test_ranking_prompt_empty_and_trainer_without_ratings(client: object) -> None:
    """Distinguish an unselected subject from an empty result and retain precision."""
    route = reverse("competency:ranking")
    assert "Choose a subject" in learning_html(client, "competency:ranking")
    subject = SubjectFactory()
    assert b"No eligible trainers" in client.get(route, {"subject": subject.pk}).content
    CompetencyFactory(subject=subject, proficiency=4)
    response = client.get(route, {"subject": subject.pk})
    html = response.content.decode()
    assert_accessible_shell(html)
    assert "4 of 5" in html and "No ratings yet" in html and 'scope="row"' in html
    assert "<caption>Trainer ranking for the selected subject</caption>" in html
