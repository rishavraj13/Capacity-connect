"""Provide bounded catalog reads for forms and list pages."""

from django.db.models import QuerySet

from apps.catalog.models import Skill, Subject


def active_subjects() -> QuerySet[Subject]:
    """Limit new selections to subjects currently offered."""
    return Subject.objects.filter(is_active=True)


def subjects_with_skills() -> QuerySet[Subject]:
    """Load each subject's skills without queries inside template loops."""
    return Subject.objects.prefetch_related("skills")


def skills_for(subject: Subject) -> QuerySet[Skill]:
    """Keep subject-specific skill reads deterministic."""
    return Skill.objects.filter(subject=subject).select_related("subject")


def selectable_skills() -> QuerySet[Skill]:
    """Exclude retired subjects from profile skill input."""
    return Skill.objects.filter(subject__is_active=True).select_related("subject")


def all_subjects() -> QuerySet[Subject]:
    """Keep administrative lookups inside the catalog read boundary."""
    return Subject.objects.all()


def all_skills() -> QuerySet[Skill]:
    """Resolve editable skills with their subject in one query."""
    return Skill.objects.select_related("subject")


def subjects_for_skill(skill: Skill) -> QuerySet[Subject]:
    """Permit retaining a retired subject while preventing new retired choices."""
    allowed = active_subjects()
    return (
        allowed | Subject.objects.filter(pk=skill.subject_id) if skill.pk else allowed
    )
