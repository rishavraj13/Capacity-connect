"""Upsert eligible trainee feedback with unique-constraint race recovery."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.services import require_approved_role
from apps.courses.models import Course
from apps.feedback.exceptions import FeedbackRuleError
from apps.feedback.models import Feedback
from apps.feedback.selectors import eligible_targets, target_filter
from apps.library.models import LibraryResource


def _save(row: Feedback) -> Feedback:
    """Validate and isolate the write so a competing insert is recoverable."""
    try:
        row.full_clean(validate_unique=False, validate_constraints=False)
        with transaction.atomic():
            row.save()
    except ValidationError as exc:
        raise FeedbackRuleError("; ".join(exc.messages)) from exc
    return row


@transaction.atomic
def _submit(trainee: User, target: object, rating: int, comment: str) -> Feedback:
    """Serialize edits and recover an insert winner without losing the new opinion."""
    trainee = require_approved_role(trainee, (UserRole.TRAINEE,))
    if (
        not eligible_targets(trainee, isinstance(target, Course))
        .filter(pk=target.pk)
        .exists()
    ):
        raise FeedbackRuleError(
            "Feedback requires an enrolled course or visible resource."
        )
    lookup = dict(author=trainee, **target_filter(target))
    return _upsert(lookup, rating, comment.strip())


def _existing(lookup: dict) -> Feedback | None:
    """Read the persisted opinion under a lock or recover a unique insert winner."""
    return Feedback.objects.select_for_update().filter(**lookup).first()


def _upsert(lookup: dict, rating: int, comment: str) -> Feedback:
    """Keep insert recovery separate from target eligibility validation."""
    row = _existing(lookup) or Feedback(**lookup)
    row.rating, row.comment = rating, comment
    try:
        return _save(row)
    except IntegrityError as exc:
        winner = _existing(lookup)
        if winner is None:
            raise FeedbackRuleError("Feedback conflict; retry.") from exc
        winner.rating, winner.comment = rating, comment
        return _save(winner)


def submit_course_feedback(
    trainee: User, course: Course, rating: int, comment: str
) -> Feedback:
    """Allow an enrolled trainee to edit one retained course opinion."""
    return _submit(trainee, course, rating, comment)


def submit_resource_feedback(
    trainee: User, resource: LibraryResource, rating: int, comment: str
) -> Feedback:
    """Allow an eligible trainee to review a published resource."""
    return _submit(trainee, resource, rating, comment)


@transaction.atomic
def delete_feedback(user: User, feedback: Feedback) -> None:
    """Let only a currently eligible author remove their opinion."""
    user = require_approved_role(user, (UserRole.TRAINEE,))
    row = Feedback.objects.select_for_update().get(pk=feedback.pk)
    if row.author_id != user.pk:
        raise FeedbackRuleError("Only the feedback author may delete it.")
    row.delete()
