"""Aggregate Admin analytics with fixed query counts and SQL best-per-pair grouping."""

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, IntegerField, Max, Q, Sum
from django.db.models.functions import Cast

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.assessments.constants import AttemptStatus
from apps.assessments.models import Attempt, Questionnaire
from apps.catalog.models import Subject
from apps.certificates.constants import Grade
from apps.certificates.models import Certificate
from apps.core.percentages import PERCENT_QUANTUM, ZERO_PERCENT, percent_for
from apps.courses.constants import EnrollmentStatus
from apps.courses.models import Course, Enrollment
from apps.dashboards.dataclasses import (
    AdminDashboard,
    AssessmentStats,
    LineLoad,
    ParticipationStats,
)

COHORT_STATUSES = (EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED)


def _users() -> tuple:
    """Count active roles and active pending approvals in one grouped query."""
    rows = (
        User.objects.order_by()
        .values("role")
        .annotate(
            active=Count("pk", filter=Q(is_active=True)),
            pending=Count("pk", filter=Q(is_active=True, is_approved=False)),
        )
    )
    roles = dict.fromkeys(UserRole.values, 0)
    pending = 0
    for row in rows:
        roles[row["role"]] = row["active"]
        pending += row["pending"]
    return roles, pending


def _enrollments() -> dict:
    """Count all historical enrollments and distinct members of the active cohort."""
    counts = {
        status: Count("pk", filter=Q(status=status))
        for status in EnrollmentStatus.values
    }
    return Enrollment.objects.aggregate(
        total=Count("pk"),
        cohort=Count("trainee_id", filter=Q(status__in=COHORT_STATUSES), distinct=True),
        **counts,
    )


def _line_load() -> tuple[LineLoad, ...]:
    """Keep zero-load active subjects and stable enrollment/name ordering."""
    rows = (
        Subject.objects.filter(is_active=True)
        .annotate(
            enrollments=Count("courses__enrollments", distinct=True),
            active_enrollments=Count(
                "courses__enrollments",
                filter=Q(courses__enrollments__status=EnrollmentStatus.ACTIVE),
                distinct=True,
            ),
        )
        .order_by("-enrollments", "name", "pk")
    )
    return tuple(
        LineLoad(row.pk, row.name, row.enrollments, row.active_enrollments)
        for row in rows
    )


def _certificates() -> tuple:
    """Count retained certificate grades, including explicit empty grade buckets."""
    grades = dict.fromkeys(Grade.values, 0)
    grades.update(
        {
            row["grade"]: row["number"]
            for row in Certificate.objects.order_by()
            .values("grade")
            .annotate(number=Count("pk"))
        }
    )
    return sum(grades.values()), grades


def _assessment_stats() -> AssessmentStats:
    """Compute best submitted pairs and their aggregate totals wholly in SQL."""
    submitted = Attempt.objects.filter(status=AttemptStatus.SUBMITTED)
    values = _best_pairs(submitted)
    number = values["number"]
    total = values["total"] or ZERO_PERCENT
    average = (
        (total / Decimal(number)).quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP)
        if number
        else ZERO_PERCENT
    )
    return AssessmentStats(
        Questionnaire.objects.count(),
        submitted.count(),
        average,
        percent_for(values["passed"] or 0, number),
    )


def _participation(enrolled: int) -> ParticipationStats:
    """Keep attempted trainees within the user-confirmed enrolled cohort."""
    cohort = Enrollment.objects.filter(status__in=COHORT_STATUSES).values("trainee_id")
    attempted = (
        Attempt.objects.filter(status=AttemptStatus.SUBMITTED, trainee_id__in=cohort)
        .values("trainee_id")
        .distinct()
        .count()
    )
    return ParticipationStats(enrolled, attempted, percent_for(attempted, enrolled))


def admin_dashboard() -> AdminDashboard:
    """Return a read-only Admin handoff in nine size-independent SQL queries."""
    roles, pending = _users()
    courses = Course.objects.aggregate(
        total=Count("pk"), published=Count("pk", filter=Q(is_published=True))
    )
    enrollments = _enrollments()
    certificates, grades = _certificates()
    return AdminDashboard(
        roles,
        pending,
        courses["total"],
        courses["published"],
        enrollments["total"],
        {status: enrollments[status] for status in EnrollmentStatus.values},
        _line_load(),
        certificates,
        grades,
        _assessment_stats(),
        _participation(enrollments["cohort"]),
    )


def _best_pairs(submitted: object) -> dict:
    """Run the best-per-pair subquery and aggregate its output in the database."""
    pairs = (
        submitted.order_by()
        .values("trainee_id", "questionnaire_id")
        .annotate(
            best_percent=Max("percent"), pair_passed=Max(Cast("passed", IntegerField()))
        )
    )
    return pairs.aggregate(
        number=Count("best_percent"),
        total=Sum("best_percent"),
        passed=Sum("pair_passed"),
    )
