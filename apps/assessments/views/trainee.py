"""Keep trainee assessment metadata, paper and results in distinct safe contexts."""

from django.db.models import Exists, OuterRef
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_safe,
)

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.assessments import selectors, services
from apps.assessments.constants import AttemptStatus
from apps.assessments.filter_forms import AssessmentFilterForm
from apps.assessments.forms import AnswerForm
from apps.assessments.models import Attempt
from apps.assessments.paper_selectors import seconds_left
from apps.assessments.readiness import ready_questionnaires
from apps.assessments.rules import expires_at
from apps.core import clock
from apps.core.exceptions import CapacityConnectError


@role_required(UserRole.TRAINEE)
@require_safe
def mine(request: HttpRequest) -> HttpResponse:
    """Combine safe departures and annotated questionnaire metadata in one page."""
    form = AssessmentFilterForm(request.user, request.GET)
    context = _listing_context(request.user, form)
    return render(request, "assessments/mine.html", context)


def _listing_context(user: object, form: AssessmentFilterForm) -> dict:
    """Apply validated filters only inside the existing enrollment scope."""
    quizzes = selectors.trainee_questionnaires(user)
    if not form.is_valid():
        return {"filter_form": form, "questionnaires": quizzes.none(), "departures": ()}
    subject = form.cleaned_data["subject"]
    if subject is not None:
        quizzes = quizzes.filter(subject=subject)
    return {
        "filter_form": form,
        "questionnaires": quizzes,
        "departures": selectors.next_deadlines_for(
            user, subject_id=subject.pk if subject else None
        ),
    }


@role_required(UserRole.TRAINEE)
@require_safe
def detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Show timing/quota only, with no question or option context."""
    ready = ready_questionnaires(OuterRef("course_id")).filter(pk=OuterRef("pk"))
    quizzes = selectors.trainee_questionnaires(request.user).annotate(
        ready=Exists(ready)
    )
    quiz = get_object_or_404(quizzes, pk=pk)
    return render(
        request,
        "assessments/detail.html",
        {"questionnaire": quiz, "start_reason": _start_reason(quiz)},
    )


def _start_reason(quiz: object) -> str:
    """Explain the current start state while the service remains authoritative."""
    instant = clock.now()
    if quiz.enrollment_status != "ACTIVE":
        return "An active enrollment is required."
    if instant < quiz.opens_at:
        return "Upcoming. The start window has not opened yet."
    if instant >= quiz.deadline:
        return "Closed. The start window has ended."
    if not quiz.attempts_left:
        return "Maximum attempts reached."
    if not quiz.ready:
        return "Questionnaire is not ready."
    return ""


@role_required(UserRole.TRAINEE)
@require_POST
def start(request: HttpRequest, pk: int) -> HttpResponse:
    """Hide quizzes outside ACTIVE enrollment before calling start/resume rules."""
    quiz = get_object_or_404(selectors.startable_questionnaires(request.user), pk=pk)
    return _start_response(request, quiz)


def _start_response(request: HttpRequest, quiz: object) -> HttpResponse:
    """Redirect successful starts while services own attempt lifecycle rules."""
    try:
        attempt = services.start_attempt(request.user, quiz)
    except CapacityConnectError as exc:
        from django.contrib import messages

        messages.error(request, exc.message)
        return redirect("assessments:detail", pk=quiz.pk)
    return redirect("assessments:take", pk=attempt.pk)


@role_required(UserRole.TRAINEE)
@require_http_methods(["GET", "POST"])
def take(request: HttpRequest, pk: int) -> HttpResponse:
    """Resolve owner identity and lazy expiry before any paper can be rendered."""
    attempt = get_object_or_404(selectors.owned_attempts(request.user), pk=pk)
    attempt = services.expire_attempt(request.user, attempt)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        return redirect("assessments:result", pk=pk)
    return _take_response(request, attempt)


def _take_response(request: HttpRequest, attempt: Attempt) -> HttpResponse:
    """Parse only radio selections and delegate all grading to the atomic service."""
    paper = selectors.paper_for(attempt)
    form = AnswerForm(paper, request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            services.submit_attempt(request.user, attempt, form.selections())
            return redirect("assessments:result", pk=attempt.pk)
        except CapacityConnectError as exc:
            form.add_error(None, exc.message)
    return render(
        request,
        "assessments/take.html",
        {
            "form": form,
            "seconds_left": seconds_left(attempt),
            "paper_rows": tuple(zip(paper, form, strict=True)),
            "paper_title": attempt.questionnaire.title,
            "submission_deadline": expires_at(attempt),
        },
    )


@role_required(*UserRole.values)
@require_safe
def result(request: HttpRequest, pk: int) -> HttpResponse:
    """Render only the selector's disclosure-filtered result dataclass."""
    result = selectors.attempt_result(request.user, pk)
    if result is None:
        raise Http404
    return render(request, "assessments/result.html", {"result": result})


@role_required(UserRole.TRAINEE)
@require_safe
def history(request: HttpRequest) -> HttpResponse:
    """Keep a trainee's take/result navigation scoped to their own history."""
    return render(
        request,
        "assessments/history.html",
        {"attempts": selectors.history_for(request.user)},
    )
