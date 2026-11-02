"""Build one trainer's course/totals handoff without per-course SQL queries."""

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, OuterRef, Q, Subquery, Sum

from apps.accounts.constants import UserRole
from apps.core.percentages import PERCENT_QUANTUM
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Course
from apps.dashboards.dataclasses import (
    CourseStats,
    QuestionnaireLink,
    TrainerDashboard,
    TrainerTotals,
)
from apps.feedback.models import Feedback


def _courses(trainer: object) -> object:
    """Keep feedback sums/counts correlated so enrollment joins cannot weight them."""
    ratings = (
        Feedback.objects.filter(course_id=OuterRef("pk"))
        .order_by()
        .values("course_id")
        .annotate(total=Sum("rating"), number=Count("pk"))
    )
    rows = Course.objects.filter(
        trainer=trainer,
        trainer__role=UserRole.TRAINER,
        trainer__is_active=True,
        trainer__is_approved=True,
    )
    return rows.annotate(
        rating_total=Subquery(ratings.values("total")[:1]),
        rating_count=Subquery(ratings.values("number")[:1]),
        **_course_counts(),
    )


def _average(total: int, count: int) -> Decimal | None:
    """Keep no-rating distinct from a zero and round exact means half up."""
    return (
        (Decimal(total) / Decimal(count)).quantize(
            PERCENT_QUANTUM, rounding=ROUND_HALF_UP
        )
        if count
        else None
    )


def _course_row(row: object) -> CourseStats:
    """Detach annotated course counts before a template can issue lazy reads."""
    return CourseStats(
        row.pk,
        row.title,
        row.is_published,
        row.enrolled,
        row.active,
        row.completed,
        row.certificates,
        _average(row.rating_total or 0, row.rating_count or 0),
        row.rating_count or 0,
        row.questionnaire_count,
    )


def trainer_dashboard(trainer: object) -> TrainerDashboard:
    """Return own-course rows and weighted totals in two fixed SQL queries."""
    raw = list(_courses(trainer))
    rows = tuple(_course_row(row) for row in raw)
    rating_count = sum(row.rating_count or 0 for row in raw)
    ratings = sum(row.rating_total or 0 for row in raw)
    totals = TrainerTotals(
        len(rows),
        sum(row.is_published for row in rows),
        sum(row.enrolled for row in rows),
        sum(row.active for row in rows),
        sum(row.completed for row in rows),
        sum(row.certificates for row in rows),
        _average(ratings, rating_count),
        rating_count,
        sum(row.questionnaires for row in rows),
    )
    return TrainerDashboard(rows, totals, _participation_links(trainer))


def _participation_links(trainer: object) -> tuple[QuestionnaireLink, ...]:
    """Fetch every own quiz link once rather than querying in a course loop."""
    from apps.assessments.selectors import managed_questionnaires

    quizzes = managed_questionnaires(trainer).filter(
        course__trainer=trainer, course__trainer__role=UserRole.TRAINER
    )
    return tuple(
        QuestionnaireLink(pk, title, course)
        for pk, title, course in quizzes.values_list("pk", "title", "course__title")
    )


def _course_counts() -> dict:
    """Group independent distinct-count annotations apart from feedback subqueries."""
    return {
        "enrolled": Count(
            "enrollments",
            filter=~Q(enrollments__status=EnrollmentStatus.DROPPED),
            distinct=True,
        ),
        "active": Count(
            "enrollments",
            filter=Q(enrollments__status=EnrollmentStatus.ACTIVE),
            distinct=True,
        ),
        "completed": Count(
            "enrollments",
            filter=Q(enrollments__status=EnrollmentStatus.COMPLETED),
            distinct=True,
        ),
        "certificates": Count("enrollments__certificate", distinct=True),
        "questionnaire_count": Count("questionnaires", distinct=True),
    }
