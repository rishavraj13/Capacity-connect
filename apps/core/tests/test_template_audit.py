"""Render classified portal routes using seeded records and real test clients."""

from collections import Counter
from io import StringIO
from pathlib import Path

import pytest
from django.apps import apps
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.assessments.tests.factories import AttemptFactory
from apps.competency.models import TrainerCompetency
from apps.core import clock
from apps.core.tests.frontend_markup import Markup, assert_accessible_shell
from apps.core.tests.journeys.isolation_routes import (
    BINDINGS,
    identifier_routes,
    target_url,
)
from apps.core.tests.route_audit import STATE_NAMES, routes
from apps.profiles.tests.factories import (
    ExternalCertificateFactory,
    QualificationFactory,
    WorkExperienceFactory,
)

UNBOUND = frozenset(
    """
styleguide announcements:home announcements:manage announcements:create
competency:mine competency:add competency:ranking dashboards:admin dashboards:trainer
feedback:mine certificates:mine certificates:verify_form certificates:verify
assessments:mine assessments:history courses:create courses:list
courses:my_courses courses:station_map
library:list library:create catalog:subject_list catalog:subject_create
catalog:skill_create
profiles:profile_list profiles:account_edit profiles:trainee_edit profiles:trainer_edit
profiles:qualification_create profiles:experience_create profiles:certificate_create
signup login trainee_home trainer_home admin_panel admin_user_list admin_pending_list
""".split()
)
FILES = {"profiles:private_file", "library:download", "certificates:download"}
PUBLIC = {"announcements:home", "certificates:verify", "certificates:verify_form"}
MODELS = {
    "announcement": "announcements.Announcement",
    "qualification": "profiles.Qualification",
    "experience": "profiles.WorkExperience",
    "certificate": "profiles.ExternalCertificate",
    "skill": "catalog.Skill",
    "resource": "library.LibraryResource",
}


class AuditMarkup(Markup):
    """Check references whose targets may occur later in the document."""

    def __init__(self) -> None:
        """Store ID counts and accessibility references in document order."""
        super().__init__()
        self.ids = Counter()
        self.references = set()
        self.tables = []
        self.controls_with_text = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Collect unique IDs and local ARIA relationships."""
        super().handle_starttag(tag, attrs)
        values = dict(attrs)
        if values.get("id"):
            self.ids[values["id"]] += 1
        for key in ("aria-labelledby", "aria-describedby"):
            self.references.update((values.get(key) or "").split())
        if tag == "table":
            self.tables.append(False)
        if tag == "caption" and self.tables:
            self.tables[-1] = True
        if tag == "th":
            assert values.get("scope") in {"row", "col", "rowgroup", "colgroup"}
        if tag in {"a", "button"}:
            self.controls_with_text.append((tag, values.get("aria-label", "")))
        if tag == "img" and self.controls_with_text:
            self.handle_data(values.get("alt") or "")

    def handle_endtag(self, tag: str) -> None:
        """Require captions and names before closing their elements."""
        super().handle_endtag(tag)
        if tag == "table":
            assert self.tables.pop(), "Missing table caption"
        if self.controls_with_text and tag == self.controls_with_text[-1][0]:
            assert self.controls_with_text.pop()[1].strip(), f"Unnamed {tag}"

    def handle_data(self, data: str) -> None:
        """Collect visible control text across nested inline tags."""
        super().handle_data(data)
        if self.controls_with_text:
            tag, label = self.controls_with_text[-1]
            self.controls_with_text[-1] = (tag, label + data)


def _seed(settings: object) -> None:
    """Run the production seed command inside pytest's disposable database."""
    settings.DEBUG = True
    settings.DEMO_PASSWORD = "Demo-Connect-2026!"
    call_command("seed_demo_data", stdout=StringIO())


def _bundle() -> dict:
    """Bind route parameters to the same seeded learning journey."""
    bundle = {
        key: apps.get_model(model).objects.first() for key, model in MODELS.items()
    }
    award = apps.get_model("certificates.Certificate").objects.first()
    enrollment = award.enrollment
    course = enrollment.course
    quiz = course.questionnaires.first()
    bundle.update(
        award=award,
        course=course,
        enrollment=enrollment,
        quiz=quiz,
        subject=course.subject,
        module=course.modules.first(),
        question=quiz.questions.first(),
        trainee=enrollment.trainee,
        trainee_profile=enrollment.trainee.trainee_profile,
        trainer_profile=course.trainer.trainer_profile,
        competency=TrainerCompetency.objects.filter(trainer=course.trainer).first(),
    )
    profile = bundle["trainee_profile"]
    bundle.update(
        qualification=QualificationFactory(profile=profile),
        experience=WorkExperienceFactory(profile=profile),
        certificate=ExternalCertificateFactory(profile=profile),
    )
    return bundle


def _clients(bundle: dict) -> dict:
    """Use approved actors linked to the selected seeded course."""
    clients = {"ANONYMOUS": Client()}
    for actor in (
        User.objects.get(username="demo_admin"),
        bundle["course"].trainer,
        bundle["trainee"],
    ):
        client = Client()
        client.force_login(actor)
        clients[actor.role] = client
    return clients


def _url(route: object, bundle: dict, keys: dict) -> str:
    """Resolve real route targets, including a distinct open paper."""
    if route.name == "certificates:verify":
        return reverse(route.name, args=[bundle["award"].certificate_id])
    if route.name == "assessments:take":
        return reverse(route.name, args=[bundle["paper"].pk])
    if route.name in BINDINGS:
        return target_url(route.name, keys[route.name], bundle)
    return route.url


def _roles(route: object) -> tuple:
    """Use route metadata while keeping the anonymous authentication forms distinct."""
    if route.name in PUBLIC:
        return ("ANONYMOUS", "TRAINEE", "TRAINER", "ADMIN")
    if route.name in {"login", "signup"}:
        return ("ANONYMOUS",)
    if route.name == "styleguide":
        return ("ANONYMOUS",)
    roles = getattr(route.callback, "allowed_roles", ())
    return tuple(
        role
        for role in roles
        if route.name != "profiles:trainee_detail" or role != "TRAINER"
    )


@pytest.mark.django_db
def test_seeded_named_html_routes(client: object, settings: object) -> None:
    """Audit all classified portal HTML and report each role-specific defect."""
    _seed(settings)
    bundle = _bundle()
    bundle["attempt"] = (
        bundle["quiz"].attempts.filter(trainee=bundle["trainee"]).first()
    )
    bundle["paper"] = AttemptFactory(
        questionnaire=bundle["quiz"], trainee=bundle["trainee"]
    )
    inventory = [
        r
        for r in routes()
        if not r.admin and not r.name.startswith("redirect:/static/")
    ]
    assert {r.name for r in inventory} == UNBOUND | STATE_NAMES | BINDINGS.keys()
    clients = _clients(bundle)
    failures, rendered = [], []
    for route in inventory:
        if route.name not in STATE_NAMES | FILES:
            _audit_route(route, bundle, clients, (failures, rendered))
    path = Path(".local/reports/F5_TEMPLATE_AUDIT.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(f"{name} [{role}]" for name, role in rendered), encoding="utf-8"
    )
    assert not failures, "\n".join(failures)


def _audit_route(route: object, bundle: dict, clients: dict, evidence: tuple) -> None:
    """Accumulate page failures so one bad template cannot hide the rest."""
    failures, rendered = evidence
    url = _url(route, bundle, identifier_routes())
    for role in _roles(route):
        with clock.at(bundle["paper"].started_at):
            response = clients[role].get(url)
        try:
            assert response.status_code == 200, response.status_code
            html = response.content.decode("utf-8")
            assert_accessible_shell(html)
            if route.name in {
                "certificates:mine",
                "certificates:verify",
                "assessments:result",
            }:
                assert 'href="/static/css/print.css" media="print"' in html
            markup = AuditMarkup()
            markup.feed(html)
            assert all(count == 1 for count in markup.ids.values()), markup.ids
            assert markup.references <= markup.ids.keys(), (
                markup.references - markup.ids.keys()
            )
        except AssertionError as exc:
            failures.append(f"{route.name} [{role}]: {exc}")
        else:
            rendered.append((route.name, role))
