"""Provide visibility-filtered course reads and bounded participant counts."""

from django.db.models import Count, Prefetch, Q, QuerySet

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Module
from apps.courses.station_maps import station_map_for as station_map_for


def visible_courses(user: User) -> QuerySet[Course]:
    """Retain trainee access to enrolled courses after unpublishing."""
    courses = Course.objects.select_related("subject", "trainer")
    if not user.is_authenticated or not user.is_active or not user.is_approved:
        return courses.none()
    if user.role == UserRole.ADMIN:
        return courses
    access = Q(is_published=True)
    if user.role == UserRole.TRAINER:
        access |= Q(trainer=user)
    if user.role == UserRole.TRAINEE:
        access |= Q(enrollments__trainee=user)
    return courses.filter(access).distinct()


def managed_courses(user: User) -> QuerySet[Course]:
    """Hide other trainers' objects before edit or participant lookups."""
    courses = visible_courses(user)
    if user.role == UserRole.ADMIN:
        return courses
    return (
        courses.filter(trainer=user)
        if user.role == UserRole.TRAINER
        else courses.none()
    )


def course_detail(user: User, pk: int) -> QuerySet[Course]:
    """Fetch all detail-page module skills without template-loop queries."""
    modules = Module.objects.prefetch_related("skills__subject")
    return (
        visible_courses(user)
        .filter(pk=pk)
        .prefetch_related(Prefetch("modules", queryset=modules))
    )


def trainer_courses(trainer: User) -> QuerySet[Course]:
    """Provide deterministic own-course choices for trainer workflows."""
    return managed_courses(trainer).filter(trainer=trainer)


def _progress_counts(enrollments: QuerySet[Enrollment]) -> QuerySet[Enrollment]:
    """Avoid inflated counts when progress and modules join the same enrollment."""
    return enrollments.select_related(
        "trainee", "course__subject", "course__trainer"
    ).annotate(
        modules_done=Count("progress", distinct=True),
        modules_total=Count("course__modules", distinct=True),
    )


def enrollments_for(trainee: User) -> QuerySet[Enrollment]:
    """Expose only a valid trainee's participation and annotated progress."""
    enrollments = Enrollment.objects.filter(trainee=trainee)
    if (
        not trainee.is_active
        or not trainee.is_approved
        or trainee.role != UserRole.TRAINEE
    ):
        return enrollments.none()
    return _progress_counts(enrollments)


def course_participants(user: User, course: Course) -> QuerySet[Enrollment]:
    """Restrict participation data to an owning trainer or Admin."""
    allowed = managed_courses(user).filter(pk=course.pk)
    return _progress_counts(Enrollment.objects.filter(course__in=allowed))


def managed_modules(user: User) -> QuerySet[Module]:
    """Resolve module ownership through the course rather than a submitted owner."""
    return Module.objects.filter(course__in=managed_courses(user)).select_related(
        "course__trainer"
    )


def detail_context(user: User, course: Course) -> dict:
    """Keep enrollment reads out of detail templates and views."""
    enrollment = (
        enrollments_for(user).filter(course=course).first()
        if user.role == UserRole.TRAINEE
        else None
    )
    return {"course": course, "enrollment": enrollment}


def enrollment_modules(enrollment: Enrollment) -> QuerySet[Module]:
    """Keep cross-course module IDs out of trainee completion requests."""
    return Module.objects.filter(course_id=enrollment.course_id)
