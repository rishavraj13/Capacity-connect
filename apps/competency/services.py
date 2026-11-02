"""Keep declarations trainer-owned, unique and bound to their original subject."""

from django.db import transaction

from apps.accounts.constants import UserRole
from apps.accounts.services import require_approved_role
from apps.catalog.selectors import active_subjects
from apps.competency.exceptions import CompetencyRuleError
from apps.competency.models import TrainerCompetency
from apps.core.services import validated_save


def _owner(trainer: object, row: TrainerCompetency) -> TrainerCompetency:
    """Recheck current eligibility and persisted row ownership before mutation."""
    current = require_approved_role(trainer, (UserRole.TRAINER,))
    row = TrainerCompetency.objects.select_for_update().get(pk=row.pk)
    if row.trainer_id != current.pk:
        raise CompetencyRuleError("Only the owning trainer may edit this declaration.")
    return row


def _values(row: TrainerCompetency, data: dict) -> None:
    """Restrict edits to declared proficiency and experience only."""
    if "subject" in data and data["subject"].pk != row.subject_id:
        raise CompetencyRuleError("The declared subject cannot change.")
    for field in ("proficiency", "years_experience"):
        if field in data:
            setattr(row, field, data[field])


@transaction.atomic
def declare_competency(
    trainer: object, subject: object, data: dict
) -> TrainerCompetency:
    """Allow only new declarations against an active subject by an eligible trainer."""
    trainer = require_approved_role(trainer, (UserRole.TRAINER,))
    if not active_subjects().filter(pk=subject.pk).exists():
        raise CompetencyRuleError("New declarations require an active subject.")
    if TrainerCompetency.objects.filter(trainer=trainer, subject=subject).exists():
        raise CompetencyRuleError("This subject is already declared.")
    row = TrainerCompetency(trainer=trainer, subject=subject)
    _values(row, data)
    validated_save(row, CompetencyRuleError)
    return row


@transaction.atomic
def update_competency(
    trainer: object, row: TrainerCompetency, data: dict
) -> TrainerCompetency:
    """Keep retired-subject declarations editable without moving their identity."""
    row = _owner(trainer, row)
    _values(row, data)
    validated_save(row, CompetencyRuleError)
    return row


@transaction.atomic
def remove_competency(trainer: object, row: TrainerCompetency) -> None:
    """Permit only the owning currently eligible trainer to remove a declaration."""
    _owner(trainer, row).delete()
