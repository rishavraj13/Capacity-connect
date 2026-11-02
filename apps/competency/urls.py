"""Name declaration and Admin ranking endpoints for explicit permission tests."""

from django.urls import path

from apps.competency import views

app_name = "competency"
urlpatterns = [
    path("mine/", views.mine, name="mine"),
    path("new/", views.add, name="add"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/remove/", views.remove, name="remove"),
    path("find-trainers/", views.ranking, name="ranking"),
]
