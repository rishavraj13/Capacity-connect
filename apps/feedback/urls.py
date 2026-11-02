"""Name each target workflow explicitly for permission coverage."""

from django.urls import path

from apps.feedback import views

app_name = "feedback"
urlpatterns = [
    path("mine/", views.mine, name="mine"),
    path("course/<int:pk>/", views.submit, {"course": True}, name="course_submit"),
    path("resource/<int:pk>/", views.submit, {"course": False}, name="resource_submit"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path(
        "course/<int:pk>/summary/",
        views.summary,
        {"course": True},
        name="course_summary",
    ),
    path(
        "resource/<int:pk>/summary/",
        views.summary,
        {"course": False},
        name="resource_summary",
    ),
]
