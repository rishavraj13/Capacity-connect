"""Expose named catalog actions for navigation and permission contracts."""

from django.urls import path

from apps.catalog import views

app_name = "catalog"
urlpatterns = [
    path("", views.subject_list, name="subject_list"),
    path("subjects/new/", views.subject_create, name="subject_create"),
    path("subjects/<int:pk>/edit/", views.subject_edit, name="subject_edit"),
    path(
        "subjects/<int:pk>/deactivate/",
        views.subject_deactivate,
        name="subject_deactivate",
    ),
    path(
        "subjects/<int:pk>/reactivate/",
        views.subject_reactivate,
        name="subject_reactivate",
    ),
    path("skills/new/", views.skill_create, name="skill_create"),
    path("skills/<int:pk>/edit/", views.skill_edit, name="skill_edit"),
    path("skills/<int:pk>/delete/", views.skill_delete, name="skill_delete"),
]
