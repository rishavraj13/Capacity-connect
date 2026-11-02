"""Keep journey actions HTTP-only after the administrator bootstrap fixture."""

from datetime import timedelta

from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.assessments.models import Question, Questionnaire
from apps.core import clock
from apps.courses.models import Course, Module

PASSWORD = "Journey-Pass-2026!"


def post(
    client: Client, name: str, data: dict | None = None, args: tuple = ()
) -> object:
    """Fail at the HTTP boundary with useful form errors rather than hide bad setup."""
    response = client.post(reverse(name, args=args), data or {})
    errors = (
        response.context["form"].errors
        if response.context and "form" in response.context
        else response.content[:500]
    )
    assert response.status_code == 302, (name, errors)
    return response


def login(user: User, password: str = PASSWORD) -> Client:
    """Authenticate through the real login form rather than force_login."""
    client = Client()
    post(client, "login", {"username": user.username, "password": password})
    return client


def signup(admin: Client, name: str, role: str = "TRAINEE") -> tuple:
    """Approve an HTTP signup through the administrator's own action endpoint."""
    visitor = Client()
    post(
        visitor,
        "signup",
        {
            "username": name,
            "email": f"{name}@example.org",
            "first_name": name.title(),
            "last_name": "Rao",
            "role": role,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
    )
    user = User.objects.get(username=name)
    post(admin, "admin_approve_user", args=(user.pk,))
    return user, login(user)


def learning_course(trainer: Client, subject_id: int) -> tuple:
    """Create and publish a course with two sequential stations through forms."""
    title = f"Journey course {Course.objects.count()}"
    post(
        trainer,
        "courses:create",
        {
            "title": title,
            "description": "Workplace learning",
            "subject": subject_id,
            "start_date": clock.today().isoformat(),
            "end_date": (clock.today() + timedelta(days=5)).isoformat(),
        },
    )
    course = Course.objects.get(title=title)
    for order in (1, 2):
        post(
            trainer,
            "courses:module_add",
            {"title": f"Station {order}", "order": order},
            (course.pk,),
        )
    post(trainer, "courses:publish", args=(course.pk,))
    return course, tuple(Module.objects.filter(course=course))


def questionnaire(trainer: Client, course: Course) -> tuple:
    """Create a ready two-choice quiz through authoring forms before attempts."""
    post(trainer, "assessments:create", quiz_data(), (course.pk,))
    quiz = Questionnaire.objects.get(course=course)
    post(
        trainer,
        "assessments:question_add",
        {
            "text": "Which is safe?",
            "options": "Validate\nIgnore",
            "correct_option": 1,
            "marks": 1,
        },
        (quiz.pk,),
    )
    return quiz, Question.objects.get(questionnaire=quiz)


def quiz_data() -> dict:
    """Use deterministic dates for the assessment authoring form."""
    return {
        "title": "Journey quiz",
        "opens_at": (clock.now() - timedelta(hours=1)).isoformat(),
        "deadline": (clock.now() + timedelta(hours=1)).isoformat(),
        "duration_minutes": 5,
        "pass_percent": 50,
        "max_attempts": 2,
    }
