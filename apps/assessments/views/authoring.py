"""Keep every authoring URL explicitly scoped to trainer ownership or Admin."""

from collections.abc import Callable
from functools import partial

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.assessments import selectors, services
from apps.assessments.forms import QuestionForm, QuestionnaireForm, question_input
from apps.core.form_views import FormAction, action_response, form_response
from apps.courses.selectors import managed_courses


def _write_question(
    actor: object, parent: object, operation: Callable, data: dict
) -> object:
    """Adapt form input without moving any authoring rules into HTTP controllers."""
    return operation(actor, parent, question_input(data))


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_safe
def course_list(request: HttpRequest, course_id: int) -> HttpResponse:
    """Hide other trainers' quiz lists through the parent course selector."""
    course = get_object_or_404(managed_courses(request.user), pk=course_id)
    quizzes = selectors.questionnaires_for_course(request.user, course)
    return render(
        request,
        "assessments/course_list.html",
        {"course": course, "questionnaires": quizzes},
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def create(request: HttpRequest, course_id: int) -> HttpResponse:
    """Create only within a managed course, deriving trainer and subject server-side."""
    course = get_object_or_404(managed_courses(request.user), pk=course_id)
    action = FormAction(
        QuestionnaireForm,
        partial(services.create_questionnaire, request.user, course),
        success_url=reverse("assessments:course_list", args=[course_id]),
        title="Create questionnaire",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Resolve ownership before validating scheduling or frozen grading fields."""
    quiz = get_object_or_404(selectors.managed_questionnaires(request.user), pk=pk)
    action = FormAction(
        QuestionnaireForm,
        partial(services.update_questionnaire, request.user, quiz),
        quiz,
        reverse("assessments:manage_detail", args=[pk]),
        "Edit questionnaire",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Leave history protection to the service after object-level filtering."""
    quiz = get_object_or_404(selectors.managed_questionnaires(request.user), pk=pk)
    return action_response(
        request,
        partial(services.delete_questionnaire, request.user, quiz),
        reverse("assessments:course_list", args=[quiz.course_id]),
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_safe
def manage_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Expose correct choices only on the role/owner-restricted authoring page."""
    quiz = get_object_or_404(selectors.authoring_detail(request.user, pk))
    return render(request, "assessments/manage_detail.html", {"questionnaire": quiz})


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def question_add(request: HttpRequest, pk: int) -> HttpResponse:
    """Keep new question ownership pinned to a managed questionnaire."""
    quiz = get_object_or_404(selectors.managed_questionnaires(request.user), pk=pk)
    action = FormAction(
        QuestionForm,
        partial(_write_question, request.user, quiz, services.add_question),
        success_url=reverse("assessments:manage_detail", args=[pk]),
        title="Add question",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
def question_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Return 404 for another trainer's question before displaying its choices."""
    question = get_object_or_404(selectors.managed_questions(request.user), pk=pk)
    form = partial(QuestionForm, initial=selectors.question_initial(question))
    action = FormAction(
        form,
        partial(_write_question, request.user, question, services.update_question),
        question,
        reverse("assessments:manage_detail", args=[question.questionnaire_id]),
        "Edit question",
    )
    return form_response(request, action)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_POST
def question_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Protect attempted questions from destructive requests at the write layer."""
    question = get_object_or_404(selectors.managed_questions(request.user), pk=pk)
    return action_response(
        request,
        partial(services.delete_question, request.user, question),
        reverse("assessments:manage_detail", args=[question.questionnaire_id]),
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
@require_safe
def participation(request: HttpRequest, pk: int) -> HttpResponse:
    """Render safe participant rows/statistics after questionnaire ownership lookup."""
    quiz = get_object_or_404(selectors.managed_questionnaires(request.user), pk=pk)
    rows, stats = selectors.participation(request.user, quiz)
    return render(
        request,
        "assessments/participation.html",
        {
            "questionnaire": quiz,
            "rows": rows,
            "stats": stats,
            "results": selectors.result_history(request.user, quiz),
        },
    )
