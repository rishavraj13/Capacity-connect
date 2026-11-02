"""Serialize station-order policy on the same course lock as first progress."""

from django.db.models import Max

from apps.courses.exceptions import CourseRuleError
from apps.courses.models import Course, Enrollment, Module, ModuleProgress


def locked_module(module: Module) -> Module:
    """Acquire the course before its module to keep lock ordering consistent."""
    current = Module.objects.get(pk=module.pk)
    Course.objects.select_for_update().get(pk=current.course_id)
    return Module.objects.select_for_update().select_related("course").get(pk=module.pk)


def lock_progress_course(enrollment: Enrollment) -> None:
    """Serialize first progress with order checks using course-first locks."""
    course_id = Enrollment.objects.values_list("course_id", flat=True).get(
        pk=enrollment.pk
    )
    Course.objects.select_for_update().get(pk=course_id)


def validate_module_order(
    course: Course, order: int, existing: Module | None = None
) -> None:
    """Freeze history once any trainee has progressed in this course."""
    if not ModuleProgress.objects.filter(module__course=course).exists():
        return
    if existing:
        if order != existing.order:
            raise CourseRuleError(
                "Module order is frozen after course progress exists."
            )
        return
    maximum = Module.objects.filter(course=course).aggregate(value=Max("order"))[
        "value"
    ]
    if order != maximum + 1:
        raise CourseRuleError("New module order must be max(order) + 1 after progress.")
