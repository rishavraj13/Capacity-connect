"""Rank eligible trainers with one joined/correlated query and exact Decimal math."""

from decimal import ROUND_HALF_UP, Decimal, localcontext

from django.db.models import Count, OuterRef, Q, Subquery, Sum, Value

from apps.accounts.constants import UserRole
from apps.competency.constants import (
    EXPERIENCE_CAP_YEARS,
    MAX_PROFICIENCY,
    MAX_RATING,
    RANK_DECIMAL_PRECISION,
    SCORE_QUANTUM,
    W_EXPERIENCE,
    W_PROFICIENCY,
    W_RATING,
)
from apps.competency.dataclasses import RankedTrainer
from apps.competency.models import TrainerCompetency
from apps.feedback.models import Feedback


def competencies_for(trainer: object) -> object:
    """Hide other declarations and ineligible users before edit/remove lookups."""
    return TrainerCompetency.objects.filter(
        trainer=trainer,
        trainer__role=UserRole.TRAINER,
        trainer__is_active=True,
        trainer__is_approved=True,
    ).select_related("subject", "trainer")


def _ranked_rows(subject: object) -> object:
    """Combine course/resource feedback over rows without averaging averages."""
    feedback = _feedback_totals(subject)
    return (
        TrainerCompetency.objects.filter(
            subject=subject,
            trainer__role=UserRole.TRAINER,
            trainer__is_active=True,
            trainer__is_approved=True,
        )
        .select_related("trainer")
        .annotate(
            rating_sum=Subquery(feedback.values("total")[:1]),
            rating_count=Subquery(feedback.values("number")[:1]),
            courses_delivered=Count(
                "trainer__courses",
                filter=Q(
                    trainer__courses__subject=subject,
                    trainer__courses__is_published=True,
                ),
                distinct=True,
            ),
        )
    )


def _score(row: object) -> tuple[Decimal, Decimal | None]:
    """Retain the unrounded score for ordering and zero only the absent rating term."""
    rating = (
        Decimal(row.rating_sum) / Decimal(row.rating_count)
        if row.rating_count
        else None
    )
    score = W_PROFICIENCY * Decimal(row.proficiency) / Decimal(MAX_PROFICIENCY)
    score += W_RATING * (rating or Decimal(0)) / Decimal(MAX_RATING)
    score += W_EXPERIENCE * min(
        Decimal(row.years_experience) / Decimal(EXPERIENCE_CAP_YEARS), Decimal(1)
    )
    return score, rating


def rank_trainers_for(subject: object) -> tuple[RankedTrainer, ...]:
    """Order unrounded scores first, then published delivery count and stable IDs."""
    with localcontext() as context:
        context.prec = RANK_DECIMAL_PRECISION
        rows = [(*_score(row), row) for row in _ranked_rows(subject)]
        rows.sort(
            key=lambda item: (-item[0], -item[2].courses_delivered, item[2].trainer_id)
        )
    return tuple(_rank_row(item, index) for index, item in enumerate(rows, 1))


def _rank_row(item: tuple, rank: int) -> RankedTrainer:
    """Return plain display values with only the score rounded to four places."""
    score, rating, row = item
    return RankedTrainer(
        row.trainer_id,
        row.trainer.get_full_name() or row.trainer.username,
        row.proficiency,
        row.years_experience,
        rating,
        row.rating_count or 0,
        row.courses_delivered,
        score.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP),
        rank,
    )


def _feedback_totals(subject: object) -> object:
    """Correlate one combined rating population per ranked trainer."""
    return (
        Feedback.objects.filter(
            Q(course__trainer_id=OuterRef("trainer_id"), course__subject=subject)
            | Q(resource__trainer_id=OuterRef("trainer_id"), resource__subject=subject)
        )
        .order_by()
        .annotate(group=Value(1))
        .values("group")
        .annotate(total=Sum("rating"), number=Count("pk"))
    )
