"""Expose private resource metadata, management and download routes."""

from django.urls import path

from apps.library import views

app_name = "library"
urlpatterns = [
    path("", views.resource_list, name="list"),
    path("new/", views.resource_create, name="create"),
    path("<int:pk>/", views.resource_detail, name="detail"),
    path("<int:pk>/edit/", views.resource_edit, name="edit"),
    path("<int:pk>/delete/", views.resource_delete, name="delete"),
    path("<int:pk>/publish/", views.resource_publish, name="publish"),
    path("<int:pk>/unpublish/", views.resource_unpublish, name="unpublish"),
    path("<int:pk>/download/", views.download, name="download"),
]
