"""Bootstrap only the initial admin; all domain actions use browser-equivalent HTTP."""

import pytest

from apps.assessments.tests.factories import MOMENT
from apps.catalog.models import Subject
from apps.core import clock
from apps.core.tests.journeys.helpers import PASSWORD, login, post, signup


@pytest.fixture
def journey(admin_user: object, monkeypatch: object, settings: object) -> tuple:
    """Supply authenticated users via HTTP while isolating clock and anti-abuse load."""
    monkeypatch.setattr(clock, "now", lambda: MOMENT)
    settings.SIGNUP_IP_LIMIT = 20
    admin_user.set_password(PASSWORD)
    admin_user.save()
    admin = login(admin_user)
    post(
        admin,
        "catalog:subject_create",
        {"name": "Journey Data", "description": "Data skills"},
    )
    subject = Subject.objects.get(name="Journey Data")
    post(
        admin,
        "catalog:skill_create",
        {"name": "Journey Validation", "subject": subject.pk},
    )
    trainer, staff = signup(admin, "ananya", "TRAINER")
    trainee, learner = signup(admin, "aarav")
    return admin, trainer, staff, trainee, learner, subject
