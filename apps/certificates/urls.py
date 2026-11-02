"""Keep certificate list/download routes distinct from public verification."""

from django.urls import path

from apps.certificates import views

app_name = "certificates"
urlpatterns = [
    path("certificates/", views.mine, name="mine"),
    path("certificates/<int:pk>/download/", views.download, name="download"),
    path("verify/", views.verify_form, name="verify_form"),
    path("verify/<str:identifier>/", views.verify, name="verify"),
]
