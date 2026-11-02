"""View controllers for authentication, onboarding, dashboards, and user management."""

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.auth_responses import login_response
from apps.accounts.constants import (
    ADMIN_USER_PAGE_SIZE,
    MSG_AWAITING_APPROVAL,
    ROLE_HOME_URL_NAMES,
    STATUS_ALL,
    UserRole,
)
from apps.accounts.forms import LoginForm, RoleChangeForm, SignupForm
from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.accounts.selectors import pending_users, users_filtered
from apps.accounts.services import approve_user, change_role, register_user, reject_user
from apps.core.exceptions import CapacityConnectError
from apps.core.rate_views import Kind, record_login_failure, throttled


def get_role_home_url(role: str) -> str:
    """Resolve home landing page route for a given user role."""
    return ROLE_HOME_URL_NAMES.get(role, "login")


@throttled(Kind.SIGNUP)
def signup_view(request: HttpRequest) -> HttpResponse:
    """Handle new user self-registration into pending approval status."""
    if request.user.is_authenticated:
        return redirect(get_role_home_url(getattr(request.user, "role", "")))
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            register_user(form.cleaned_data)
            messages.success(request, MSG_AWAITING_APPROVAL)
            return redirect("login")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


@throttled(Kind.LOGIN)
def login_view(request: HttpRequest) -> HttpResponse:
    """Authenticate existing approved users and direct to designated portal home."""
    if request.user.is_authenticated:
        return redirect(get_role_home_url(getattr(request.user, "role", "")))
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            return login_response(request, form.get_user())
        record_login_failure(request)
    else:
        form = LoginForm(request)
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Terminate authenticated session restricted to POST submissions."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    auth_logout(request)
    return redirect("login")


@role_required(UserRole.TRAINEE)
def trainee_home(request: HttpRequest) -> HttpResponse:
    """Render trainee dashboard landing page."""
    return render(request, "accounts/trainee_home.html")


@role_required(UserRole.TRAINER)
def trainer_home(request: HttpRequest) -> HttpResponse:
    """Render trainer dashboard landing page."""
    return render(request, "accounts/trainer_home.html")


@role_required(UserRole.ADMIN)
def admin_panel(request: HttpRequest) -> HttpResponse:
    """Render administrator dashboard landing page."""
    return render(request, "accounts/admin_panel.html")


@role_required(UserRole.ADMIN)
def admin_user_list(request: HttpRequest) -> HttpResponse:
    """Display paginated list of all users filtered by role and account status."""
    role: str = request.GET.get("role", STATUS_ALL)
    status: str = request.GET.get("status", STATUS_ALL)
    users_qs = users_filtered(role=role, status=status)
    paginator = Paginator(users_qs, ADMIN_USER_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/admin_user_list.html",
        {
            "page_obj": page_obj,
            "selected_role": role,
            "selected_status": status,
            "role_choices": UserRole.choices,
        },
    )


@role_required(UserRole.ADMIN)
def admin_pending_list(request: HttpRequest) -> HttpResponse:
    """Display list of applicants awaiting administrator review and approval."""
    users = pending_users()
    return render(
        request,
        "accounts/admin_pending_list.html",
        {"pending_users": users},
    )


@role_required(UserRole.ADMIN)
def admin_approve_user(request: HttpRequest, user_id: int) -> HttpResponse:
    """Approve applicant account granting access to portal resources."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    target: User = get_object_or_404(User, pk=user_id)
    approve_user(target, request.user)
    messages.success(request, f"User {target.username} has been approved.")
    return redirect(request.POST.get("next", "admin_pending_list"))


@role_required(UserRole.ADMIN)
def admin_reject_user(request: HttpRequest, user_id: int) -> HttpResponse:
    """Reject and disable applicant account preventing further access."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    target: User = get_object_or_404(User, pk=user_id)
    try:
        reject_user(target, request.user)
        messages.success(request, f"User {target.username} has been rejected.")
    except CapacityConnectError as exc:
        messages.error(request, exc.message)
    return redirect(request.POST.get("next", "admin_user_list"))


@role_required(UserRole.ADMIN)
def admin_change_role(request: HttpRequest, user_id: int) -> HttpResponse:
    """Modify designated role of target user subject to security restrictions."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    target: User = get_object_or_404(User, pk=user_id)
    form = RoleChangeForm(request.POST)
    if form.is_valid():
        try:
            change_role(target, form.cleaned_data["role"], request.user)
            messages.success(request, f"Role for {target.username} updated.")
        except CapacityConnectError as exc:
            messages.error(request, exc.message)
    return redirect(request.POST.get("next", "admin_user_list"))
