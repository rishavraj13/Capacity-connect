"""URL route configuration for accounts and administrative features."""

from django.urls import path

from apps.accounts import views

urlpatterns: list = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("trainee/", views.trainee_home, name="trainee_home"),
    path("trainer/", views.trainer_home, name="trainer_home"),
    path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("admin-panel/users/", views.admin_user_list, name="admin_user_list"),
    path(
        "admin-panel/pending/",
        views.admin_pending_list,
        name="admin_pending_list",
    ),
    path(
        "admin-panel/users/<int:user_id>/approve/",
        views.admin_approve_user,
        name="admin_approve_user",
    ),
    path(
        "admin-panel/users/<int:user_id>/reject/",
        views.admin_reject_user,
        name="admin_reject_user",
    ),
    path(
        "admin-panel/users/<int:user_id>/change-role/",
        views.admin_change_role,
        name="admin_change_role",
    ),
]
