"""Scope feedback reads and build anonymous staff presentation data."""

from decimal import ROUND_HALF_UP, Decimal

from django.core.paginator import Page, Paginator
from django.db.models import Count, QuerySet

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.courses.models import Course, Enrollment
from apps.courses.selectors import managed_courses
from apps.feedback.constants import MAX_RATING, MIN_RATING, PAGE_SIZE, RATING_QUANTUM
from apps.feedback.dataclasses import FeedbackRow, FeedbackSummary
from apps.feedback.models import Feedback
from apps.library.models import LibraryResource
from apps.library.selectors import managed_resources, visible_resources


def target_filter(target: Course | LibraryResource) -> dict:
    """Choose only known target types for shared summary/write operations."""
    return {"course" if isinstance(target, Course) else "resource": target}


def feedback_summary(target: Course | LibraryResource) -> FeedbackSummary:
    """Aggregate buckets in one query without binary floating point averages."""
    grouped = (
        Feedback.objects.filter(**target_filter(target))
        .order_by()
        .values("rating")
        .annotate(count=Count("pk"))
    )
    distribution = dict.fromkeys(range(MIN_RATING, MAX_RATING + 1), 0)
    distribution.update({row["rating"]: row["count"] for row in grouped})
    count = sum(distribution.values())
    total = sum(rating * number for rating, number in distribution.items())
    average = (Decimal(total) / Decimal(count) if count else Decimal(0)).quantize(
        RATING_QUANTUM, rounding=ROUND_HALF_UP
    )
    return FeedbackSummary(count, average, distribution)


def feedback_for_trainee(trainee: User) -> QuerySet[Feedback]:
    """Keep own feedback targets joined for list/edit/delete navigation."""
    rows = Feedback.objects.select_related("course", "resource").filter(author=trainee)
    return (
        rows
        if trainee.is_active
        and trainee.is_approved
        and trainee.role == UserRole.TRAINEE
        else rows.none()
    )


def feedback_page(
    user: User, target: Course | LibraryResource, page: object = 1
) -> Page | None:
    """Authorize first, then drop author identity from trainer-visible DTOs."""
    if (
        not managed_targets(user, isinstance(target, Course))
        .filter(pk=target.pk)
        .exists()
    ):
        return None
    rows = Feedback.objects.filter(**target_filter(target)).select_related("author")
    result = Paginator(rows, PAGE_SIZE).get_page(page)
    reveal = user.role == UserRole.ADMIN
    result.object_list = [
        FeedbackRow(
            row.rating,
            row.comment,
            (row.author.get_full_name() or row.author.username) if reveal else None,
        )
        for row in result.object_list
    ]
    return result


def managed_targets(user: User, course: bool) -> QuerySet:
    """Resolve target ownership before summary views disclose any comments."""
    return managed_courses(user) if course else managed_resources(user)


def eligible_targets(trainee: User, course: bool) -> QuerySet:
    """Retain course feedback for any historical enrollment status."""
    if course:
        return Course.objects.filter(
            enrollments__in=Enrollment.objects.filter(trainee=trainee)
        )
    return visible_resources(trainee).filter(is_published=True)
