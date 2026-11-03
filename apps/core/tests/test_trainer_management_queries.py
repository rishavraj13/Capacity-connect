"""Count real trainer and administrator responses at two fixture sizes."""

from functools import partial

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SkillFactory, SubjectFactory
from apps.competency.tests.factories import CompetencyFactory
from apps.core.tests.query_pages import PageSetup, assert_stable_page
from apps.courses.tests.factories import CourseFactory, ModuleFactory
from apps.library.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "route",
    (
        "trainer_home",
        "courses:create",
        "courses:edit",
        "courses:module_add",
        "courses:module_edit",
        "library:create",
        "library:edit",
        "competency:mine",
        "competency:add",
        "competency:edit",
    ),
)
def test_trainer_editor_query_count_stays_constant(client: object, route: str) -> None:
    """Grow available subjects without adding queries to the target response."""
    course = CourseFactory()
    module = ModuleFactory(course=course)
    resource = ResourceFactory(trainer=course.trainer)
    row = CompetencyFactory(trainer=course.trainer)
    args = {
        "courses:edit": (course.pk,),
        "courses:module_add": (course.pk,),
        "courses:module_edit": (module.pk,),
        "library:edit": (resource.pk,),
        "competency:edit": (row.pk,),
    }.get(route, ())
    setup = PageSetup(
        reverse(route, args=args),
        course.trainer,
        partial(SubjectFactory.create_batch, 9),
    )
    assert_stable_page(client, route, setup)


@pytest.mark.parametrize("role", ("owner", "admin"))
@pytest.mark.parametrize(
    "name", ("courses:list", "courses:detail", "library:list", "library:detail")
)
def test_shared_management_queries_stay_constant(
    client: object, role: str, name: str
) -> None:
    """Grow real list entries and module rows under each staff view branch."""
    course = CourseFactory(is_published=True)
    module = ModuleFactory(course=course)
    module.skills.add(SkillFactory())
    row = ResourceFactory(trainer=course.trainer, is_published=True)
    user = course.trainer if role == "owner" else UserFactory(active_admin=True)
    args = {"courses:detail": (course.pk,), "library:detail": (row.pk,)}.get(name, ())
    grow = {
        "courses:list": partial(CourseFactory.create_batch, 9, trainer=course.trainer),
        "courses:detail": partial(_add_modules_with_skills, course),
        "library:list": partial(
            ResourceFactory.create_batch, 9, trainer=course.trainer
        ),
        "library:detail": partial(
            ResourceFactory.create_batch, 9, trainer=course.trainer
        ),
    }[name]
    assert_stable_page(
        client, f"{role} {name}", PageSetup(reverse(name, args=args), user, grow)
    )


def _add_modules_with_skills(course: object) -> None:
    """Exercise both displayed skill names and the interchange badge."""
    for module in ModuleFactory.create_batch(9, course=course):
        module.skills.add(SkillFactory(), SkillFactory())
