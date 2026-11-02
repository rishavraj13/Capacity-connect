"""Root URL configuration for Capacity Connect."""

from django.contrib import admin
from django.urls import include, path

urlpatterns: list = [
    path("courses/", include("apps.courses.urls")),
    path("library/", include("apps.library.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("profiles/", include("apps.profiles.urls")),
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
]
