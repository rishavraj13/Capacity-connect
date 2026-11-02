"""Exercise real enrollment, attempt, completion and private-upload workflows."""

from datetime import timedelta

from apps.assessments.dataclasses import QuestionInput
from apps.assessments.services import (
    add_question,
    create_questionnaire,
    start_attempt,
    submit_attempt,
)
from apps.core import clock
from apps.core.demo_constants import (
    APPROVED_TRAINEES,
    DEMO_DURATION_MINUTES,
    DEMO_LOOKBACK_DAYS,
    DEMO_MAX_ATTEMPTS,
    DEMO_PREFIX,
    DEMO_WINDOW_DAYS,
)
from apps.core.demo_files import demo_pdf, demo_png
from apps.courses.services import complete_module, drop, enroll
from apps.library.services import create_resource
from apps.library.services import publish as publish_resource
from apps.profiles.services import (
    ensure_trainee_profile,
    ensure_trainer_profile,
    update_trainee_profile,
    update_trainer_profile,
)


def demo_profiles(graph: object) -> None:
    """Store the agreed PNG in a profile while keeping library types unchanged."""
    for trainer in graph.trainers:
        update_trainer_profile(
            ensure_trainer_profile(trainer),
            {
                "bio": "Practical skills trainer.",
                "headline": "Learn by doing",
                "years_experience": 10,
            },
        )
    for index, trainee in enumerate(graph.trainees):
        data = {
            "bio": "Learning practical workplace skills.",
            "skills": [graph.skills[0][0]],
        }
        if index == 0:
            data["photo"] = demo_png()
        update_trainee_profile(ensure_trainee_profile(trainee), data)


def demo_assessments(graph: object) -> None:
    """Create one ready quiz and one empty draft before any attempt freezes terms."""
    course = graph.courses[0]
    data = {
        "title": DEMO_PREFIX + "Digital skills check",
        "opens_at": clock.now() - timedelta(days=DEMO_LOOKBACK_DAYS),
        "deadline": clock.now() + timedelta(days=DEMO_WINDOW_DAYS),
        "duration_minutes": DEMO_DURATION_MINUTES,
        "pass_percent": 50,
        "max_attempts": DEMO_MAX_ATTEMPTS,
    }
    graph.quiz = create_questionnaire(course.trainer, course, data)
    graph.question = add_question(
        course.trainer,
        graph.quiz,
        QuestionInput(
            "How should you check a new dataset?",
            ("Validate the data carefully", "Skip validation"),
            0,
            1,
        ),
    )
    create_questionnaire(
        course.trainer, course, {**data, "title": DEMO_PREFIX + "Draft skills check"}
    )


def demo_progress(graph: object) -> None:
    """Populate DONE/CURRENT/LOCKED, all-done ACTIVE and dropped retained histories."""
    graph.enrollments = [
        enroll(user, graph.courses[0]) for user in graph.trainees[:APPROVED_TRAINEES]
    ]
    for index in (0, 4):
        for module in graph.modules[0]:
            complete_module(graph.trainees[index], graph.enrollments[index], module)
    for index in (3, 5):
        complete_module(
            graph.trainees[index], graph.enrollments[index], graph.modules[0][0]
        )
    drop(graph.trainees[5], graph.enrollments[5])
    for index in range(1, 4):
        enrollment = enroll(graph.trainees[index + 5], graph.courses[index])
        if index == 1:
            complete_module(enrollment.trainee, enrollment, graph.modules[index][0])
    _attempts(graph)


def _attempts(graph: object) -> None:
    """Produce passed/failed/timed-out outcomes through the clock-aware services."""
    correct = graph.question.options.order_by("pk").first().pk
    wrong = graph.question.options.order_by("pk").last().pk
    for index, option in ((0, correct), (1, wrong)):
        user = graph.trainees[index]
        attempt = start_attempt(user, graph.quiz)
        submit_attempt(user, attempt, {graph.question.pk: option})
    instant = clock.now()
    with clock.at(instant - timedelta(minutes=10)):
        attempt = start_attempt(graph.trainees[2], graph.quiz)
    submit_attempt(graph.trainees[2], attempt, {})


def demo_resources(graph: object) -> None:
    """Create a published workbook and private draft through actual upload services."""
    for index in range(2):
        course = graph.courses[index]
        resource = create_resource(
            course.trainer,
            {
                "subject": course.subject,
                "course": course,
                "title": DEMO_PREFIX + f"Workbook {index + 1}",
                "kind": "DOCUMENT",
                "file": demo_pdf(),
                "description": "A short practice workbook.",
            },
        )
        if index == 0:
            graph.resource = publish_resource(course.trainer, resource)
