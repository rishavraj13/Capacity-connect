"""Name public and managed routes separately for permission coverage."""

from django.urls import path

from apps.announcements import views

app_name = "announcements"
urlpatterns = [
    path("", views.home, name="home"),
    path("announcements/manage/", views.manage, name="manage"),
    path("announcements/new/", views.create, name="create"),
    path("announcements/<int:pk>/edit/", views.edit, name="edit"),
    path("announcements/<int:pk>/publish/", views.publish, name="publish"),
    path("announcements/<int:pk>/unpublish/", views.unpublish, name="unpublish"),
    path("announcements/<int:pk>/delete/", views.delete, name="delete"),
]
