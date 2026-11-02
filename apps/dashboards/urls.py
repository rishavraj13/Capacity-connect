"""Keep analytics endpoints distinct from unchanged role landing names."""

from django.urls import path

from apps.dashboards import views

app_name = "dashboards"
urlpatterns = [
    path("admin/", views.admin, name="admin"),
    path("trainer/", views.trainer, name="trainer"),
]
