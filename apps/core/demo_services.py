"""Seed an idempotent service-driven demo with an explicit production guard."""

import os

from django.conf import settings
from django.db import transaction

from apps.announcements.constants import Category
from apps.announcements.services import create, publish
from apps.core import clock
from apps.core.demo_accounts import demo_accounts
from apps.core.demo_catalog import demo_catalog, demo_courses
from apps.core.demo_constants import DEMO_MARKER
from apps.core.demo_learning import (
    demo_assessments,
    demo_profiles,
    demo_progress,
    demo_resources,
)
from apps.core.demo_selectors import demo_exists, demo_summary
from apps.core.exceptions import CapacityConnectError
from apps.feedback.services import submit_course_feedback, submit_resource_feedback


def _posts(graph: object) -> None:
    """Create every demo category and final marker through Admin services."""
    for category in Category.values:
        row = create(
            graph.admin,
            {
                "title": f"Demo {Category(category).label}",
                "body": "Build skills through practical learning.",
                "category": category,
            },
        )
        if category != Category.DEADLINE:
            publish(graph.admin, row)
    publish(
        graph.admin,
        create(
            graph.admin,
            {
                "title": DEMO_MARKER,
                "body": "Explore courses, practice activities and learning milestones.",
                "category": Category.NOTICE,
            },
        ),
    )


def _feedback(graph: object) -> None:
    """Exercise completed, active and dropped course feedback plus a public resource."""
    for index, rating in ((0, 5), (1, 4), (5, 3)):
        submit_course_feedback(
            graph.trainees[index],
            graph.courses[0],
            rating,
            "Useful practice and clear examples.",
        )
    submit_resource_feedback(graph.trainees[3], graph.resource, 5, "Helpful workbook.")


@transaction.atomic
def seed_demo_data(force: bool = False) -> dict:
    """Refuse unsafe environments unless explicitly forced; reruns perform no writes."""
    if not force and (
        not settings.DEBUG
        or os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith(".prod")
    ):
        raise CapacityConnectError(
            "Demo seeding requires DEBUG=True outside prod, or explicit --force."
        )
    if demo_exists():
        return demo_summary()
    with clock.at(clock.now()):
        graph = demo_accounts(settings.DEMO_PASSWORD)
        demo_catalog(graph)
        demo_courses(graph)
        demo_profiles(graph)
        demo_assessments(graph)
        demo_progress(graph)
        demo_resources(graph)
        _feedback(graph)
        _posts(graph)
    return demo_summary()
