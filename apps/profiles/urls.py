"""Expose stable profile routes without public media URLs."""

from django.urls import path

from apps.profiles.views import children, files, profiles

app_name = "profiles"
urlpatterns = [
    path("", profiles.profile_list, name="profile_list"),
    path("account/", profiles.account_edit, name="account_edit"),
    path("trainee/edit/", profiles.trainee_edit, name="trainee_edit"),
    path("trainer/edit/", profiles.trainer_edit, name="trainer_edit"),
    path("trainee/<int:pk>/", profiles.trainee_detail, name="trainee_detail"),
    path("trainer/<int:pk>/", profiles.trainer_detail, name="trainer_detail"),
    path("files/<str:kind>/<int:pk>/", files.private_file, name="private_file"),
    path(
        "qualification/new/", children.qualification_create, name="qualification_create"
    ),
    path(
        "qualification/<int:pk>/edit/",
        children.qualification_edit,
        name="qualification_edit",
    ),
    path(
        "qualification/<int:pk>/delete/",
        children.qualification_delete,
        name="qualification_delete",
    ),
    path("experience/new/", children.experience_create, name="experience_create"),
    path("experience/<int:pk>/edit/", children.experience_edit, name="experience_edit"),
    path(
        "experience/<int:pk>/delete/",
        children.experience_delete,
        name="experience_delete",
    ),
    path("certificate/new/", children.certificate_create, name="certificate_create"),
    path(
        "certificate/<int:pk>/edit/", children.certificate_edit, name="certificate_edit"
    ),
    path(
        "certificate/<int:pk>/delete/",
        children.certificate_delete,
        name="certificate_delete",
    ),
]
