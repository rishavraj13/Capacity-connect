"""Expose stable course-management and trainee-participation route names."""

from django.urls import path

from apps.courses.views import management, participation

app_name = "courses"
urlpatterns = [
    path("", management.course_list, name="list"),
    path("new/", management.course_create, name="create"),
    path("mine/", participation.my_courses, name="my_courses"),
    path("stations/", participation.station_map, name="station_map"),
    path("<int:pk>/", management.course_detail, name="detail"),
    path("<int:pk>/edit/", management.course_edit, name="edit"),
    path("<int:pk>/publish/", management.course_publish, name="publish"),
    path("<int:pk>/unpublish/", management.course_unpublish, name="unpublish"),
    path("<int:pk>/modules/new/", management.module_add, name="module_add"),
    path("modules/<int:pk>/edit/", management.module_edit, name="module_edit"),
    path("modules/<int:pk>/delete/", management.module_delete, name="module_delete"),
    path("<int:pk>/enroll/", participation.enroll, name="enroll"),
    path("enrollments/<int:pk>/drop/", participation.drop, name="drop"),
    path(
        "enrollments/<int:pk>/modules/<int:module_id>/complete/",
        participation.complete_module,
        name="complete_module",
    ),
    path("<int:pk>/participants/", management.course_participants, name="participants"),
]
