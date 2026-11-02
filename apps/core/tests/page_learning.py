"""Grow course, library and station-map populations behind rendered pages."""

from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import QuestionFactory
from apps.catalog.tests.factories import SkillFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.core.tests.query_pages import PageSetup
from apps.courses.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    ModuleFactory,
    ModuleProgressFactory,
)
from apps.library.tests.factories import ResourceFactory


def _enrolled_course(user: object) -> object:
    """Populate a course with modules/skills/progress for every course-list handoff."""
    enrollment = EnrollmentFactory(trainee=user, course__is_published=True)
    module = ModuleFactory(course=enrollment.course, order=1)
    module.skills.add(SkillFactory())
    ModuleProgressFactory(enrollment=enrollment, module=module)
    return enrollment


def course_list(name: str) -> PageSetup:
    """Grow courses and participation while preserving a valid trainee actor."""
    user = UserFactory(approved_trainee=True)
    _enrolled_course(user)
    return PageSetup(
        reverse(name), user, lambda: [_enrolled_course(user) for _ in range(9)]
    )


def course_detail() -> PageSetup:
    """Grow the displayed modules, their skills and ready quizzes in one course."""
    user = UserFactory(approved_trainee=True)
    enrollment = _enrolled_course(user)
    QuestionFactory(questionnaire__course=enrollment.course)

    def expand() -> None:
        """Exercise nested module/skill rendering and the completion status handoff."""
        for order in range(2, 11):
            module = ModuleFactory(course=enrollment.course, order=order)
            module.skills.add(SkillFactory(), SkillFactory())
            QuestionFactory(questionnaire__course=enrollment.course)

    return PageSetup(
        reverse("courses:detail", args=[enrollment.course_id]), user, expand
    )


def participants() -> PageSetup:
    """Grow participant rows including certificate links without lazy row reads."""
    course = CourseFactory(is_published=True)
    module = ModuleFactory(course=course)

    def add() -> None:
        """Populate progress and certificates on every participant row."""
        enrollment = EnrollmentFactory(course=course, status="COMPLETED")
        ModuleProgressFactory(enrollment=enrollment, module=module)
        CertificateFactory(enrollment=enrollment)

    add()
    return PageSetup(
        reverse("courses:participants", args=[course.pk]),
        course.trainer,
        lambda: [add() for _ in range(9)],
    )


def library_page(detail: bool) -> PageSetup:
    """Keep linked course visibility active for both resource list/detail sizes."""
    user = UserFactory(approved_trainee=True)
    course = CourseFactory(is_published=True)

    def add() -> object:
        """Add a published resource with a real private file and course association."""
        return ResourceFactory(
            course=course,
            trainer=course.trainer,
            subject=course.subject,
            is_published=True,
        )

    row = add()
    url = (
        reverse("library:detail", args=[row.pk]) if detail else reverse("library:list")
    )
    return PageSetup(url, user, lambda: [add() for _ in range(9)])
