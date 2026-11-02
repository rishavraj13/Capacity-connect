"""Create demo catalog, declarations and courses only through domain services."""

from datetime import timedelta

from apps.catalog.services import create_skill, create_subject
from apps.competency.services import declare_competency
from apps.core import clock
from apps.core.demo_constants import (
    COURSE_NAMES,
    DEMO_LOOKBACK_DAYS,
    DEMO_PREFIX,
    DEMO_WINDOW_DAYS,
    MODULE_TITLES,
    SUBJECT_NAMES,
)
from apps.courses.services import add_module, create_course, publish


def demo_catalog(graph: object) -> None:
    """Build four subject lines with globally unique skill names."""
    for name in SUBJECT_NAMES:
        subject = create_subject(
            {"name": DEMO_PREFIX + name, "description": "Practice, learn and apply."}
        )
        skills = [
            create_skill({"name": f"{DEMO_PREFIX}{name} {suffix}", "subject": subject})
            for suffix in ("Basics", "Practice")
        ]
        graph.subjects.append(subject)
        graph.skills.append(skills)
    for index, trainer in enumerate(graph.trainers):
        for subject in graph.subjects[:2]:
            declare_competency(
                trainer,
                subject,
                {"proficiency": 5 - index, "years_experience": 10 - index * 3},
            )


def demo_courses(graph: object) -> None:
    """Populate all modules before progress can freeze station ordering."""
    today = clock.today()
    for index, title in enumerate(COURSE_NAMES):
        trainer = graph.trainers[index % len(graph.trainers)]
        subject = graph.subjects[index % len(graph.subjects)]
        course = create_course(
            trainer,
            {
                "title": DEMO_PREFIX + title,
                "description": "A practical learning path.",
                "subject": subject,
                "start_date": today - timedelta(days=DEMO_LOOKBACK_DAYS),
                "end_date": today + timedelta(days=DEMO_WINDOW_DAYS),
            },
        )
        graph.courses.append(course)
        graph.modules.append(_modules(graph, course, index))
        if index < len(COURSE_NAMES) - 1:
            publish(trainer, course)


def _modules(graph: object, course: object, index: int) -> list:
    """Give the first course an interchange spanning two subject skill sets."""
    result = []
    for order, title in enumerate(MODULE_TITLES, 1):
        skills = [graph.skills[index % len(graph.skills)][0]]
        if index == 0 and order == 2:
            skills.append(graph.skills[2][0])
        result.append(
            add_module(
                course.trainer,
                course,
                {"title": title, "order": order, "skills": skills},
            )
        )
    return result
