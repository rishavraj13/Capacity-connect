"""Expose authoring, participation and trainee attempt route names explicitly."""

from django.urls import path

from apps.assessments.views import authoring, trainee

app_name = "assessments"
urlpatterns = [
    path("courses/<int:course_id>/", authoring.course_list, name="course_list"),
    path("courses/<int:course_id>/new/", authoring.create, name="create"),
    path("<int:pk>/manage/", authoring.manage_detail, name="manage_detail"),
    path("<int:pk>/edit/", authoring.edit, name="edit"),
    path("<int:pk>/delete/", authoring.delete, name="delete"),
    path("<int:pk>/questions/new/", authoring.question_add, name="question_add"),
    path("questions/<int:pk>/edit/", authoring.question_edit, name="question_edit"),
    path(
        "questions/<int:pk>/delete/", authoring.question_delete, name="question_delete"
    ),
    path("<int:pk>/participation/", authoring.participation, name="participation"),
    path("mine/", trainee.mine, name="mine"),
    path("history/", trainee.history, name="history"),
    path("<int:pk>/", trainee.detail, name="detail"),
    path("<int:pk>/start/", trainee.start, name="start"),
    path("attempts/<int:pk>/take/", trainee.take, name="take"),
    path("attempts/<int:pk>/result/", trainee.result, name="result"),
]
