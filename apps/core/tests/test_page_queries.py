"""Enforce equal SMALL/LARGE query counts for every application list/detail page."""

from functools import partial

import pytest

from apps.core.tests.page_accounts import (
    account_list,
    catalog_list,
    profile_directory,
    trainee_detail,
    trainer_detail,
)
from apps.core.tests.page_assessments import attempt_result, staff_page, trainee_page
from apps.core.tests.page_learning import (
    course_detail,
    course_list,
    library_page,
    participants,
)
from apps.core.tests.page_other import (
    announcement_page,
    certificate_page,
    competency_page,
    dashboard_page,
    feedback_page,
)
from apps.core.tests.query_pages import assert_stable_page

RECIPES = {
    "accounts users": partial(account_list, "admin_user_list"),
    "accounts pending": partial(account_list, "admin_pending_list"),
    "catalog list": catalog_list,
    "profile directory": profile_directory,
    "trainee detail": trainee_detail,
    "trainer detail": trainer_detail,
    "courses list": partial(course_list, "courses:list"),
    "course detail": course_detail,
    "my courses": partial(course_list, "courses:my_courses"),
    "station map": partial(course_list, "courses:station_map"),
    "participants": participants,
    "library list": partial(library_page, False),
    "library detail": partial(library_page, True),
    "assessments mine": partial(trainee_page, "assessments:mine"),
    "assessment detail": partial(trainee_page, "assessments:detail"),
    "assessment history": partial(trainee_page, "assessments:history"),
    "assessment participation": partial(staff_page, "assessments:participation"),
    "assessment result": attempt_result,
    "assessment authoring list": partial(staff_page, "assessments:course_list"),
    "assessment authoring detail": partial(staff_page, "assessments:manage_detail"),
    "feedback mine": partial(feedback_page, "mine"),
    "course feedback trainer": partial(feedback_page, "course"),
    "course feedback admin": partial(feedback_page, "course", True),
    "resource feedback trainer": partial(feedback_page, "resource"),
    "resource feedback admin": partial(feedback_page, "resource", True),
    "certificates mine": certificate_page,
    "public verification": partial(certificate_page, True),
    "announcements home": announcement_page,
    "announcements manage": partial(announcement_page, True),
    "competency mine": competency_page,
    "competency ranking": partial(competency_page, True),
    "admin dashboard": partial(dashboard_page, True),
    "trainer dashboard": dashboard_page,
}


@pytest.mark.django_db
@pytest.mark.parametrize("name", RECIPES)
def test_every_page_has_constant_queries(client: object, name: str) -> None:
    """Catch N+1 growth in the complete response including auth and templates."""
    assert_stable_page(client, name, RECIPES[name]())
