"""Verify catalog rules at database, service, selector and form boundaries."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.catalog import selectors, services
from apps.catalog.forms import SkillForm, SubjectForm
from apps.catalog.models import Skill, Subject
from apps.catalog.tests.factories import SkillFactory, SubjectFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "factory,model", [(SubjectFactory, Subject), (SkillFactory, Skill)]
)
def test_database_names_are_case_insensitive(factory: type, model: type) -> None:
    """Guarantee uniqueness even when forms and services are bypassed."""
    item = factory(name="Mixed Case")
    values = {"name": "MIXED CASE"}
    if model is Skill:
        values["subject"] = item.subject
    with pytest.raises(IntegrityError), transaction.atomic():
        model.objects.create(**values)
    assert str(item) == "Mixed Case"


def test_subject_is_protected_and_lifecycle_is_reversible() -> None:
    """Retain subject references while controlling future skill creation."""
    subject = services.create_subject({"name": "Science", "is_active": False})
    assert subject.is_active
    skill = services.create_skill({"name": "Logic", "subject": subject})
    with pytest.raises(ProtectedError):
        subject.delete()
    services.deactivate_subject(subject)
    with pytest.raises(ValidationError):
        services.create_skill({"name": "New", "subject": subject})
    services.reactivate_subject(subject)
    services.update_subject(subject, {"name": "Sciences", "description": "Updated"})
    services.update_skill(skill, {"name": "Reasoning", "subject": subject})
    assert subject.name == "Sciences" and skill.name == "Reasoning"
    services.delete_skill(skill)
    assert not Skill.objects.exists()


def test_skill_moves_require_active_target() -> None:
    """Reject stale or inactive destinations at the service boundary."""
    skill = SkillFactory()
    retired = SubjectFactory(is_active=False)
    with pytest.raises(ValidationError):
        services.update_skill(skill, {"name": skill.name, "subject": retired})
    target = SubjectFactory()
    services.update_skill(skill, {"name": "Moved", "subject": target})
    assert skill.subject == target


def test_catalog_selectors_have_bounded_queries(
    django_assert_num_queries: object,
) -> None:
    """Make query costs independent of the number of subjects."""
    SkillFactory.create_batch(4)
    retired = SubjectFactory(is_active=False)
    with django_assert_num_queries(2):
        subjects = list(selectors.subjects_with_skills())
        assert sum(len(subject.skills.all()) for subject in subjects) == 4
    assert retired not in selectors.active_subjects()
    skill = Skill.objects.first()
    assert list(selectors.skills_for(skill.subject)) == [skill]


def test_catalog_forms_validate_names_and_limit_fields() -> None:
    """Give useful validation while preventing lifecycle mass assignment."""
    subject = SubjectFactory(name="Science")
    assert not SubjectForm({"name": "SCIENCE"}).is_valid()
    assert set(SubjectForm().fields) == {"name", "description"}
    skill = SkillFactory(subject=subject)
    assert not SkillForm({"name": skill.name.upper(), "subject": subject.pk}).is_valid()
    services.deactivate_subject(subject)
    assert not SkillForm({"name": "New", "subject": subject.pk}).is_valid()
    assert SkillForm(
        {"name": "Renamed", "subject": subject.pk}, instance=skill
    ).is_valid()
