"""Root URL configuration for Capacity Connect."""

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from apps.core.styleguide import styleguide

urlpatterns: list = [
    path("styleguide/", styleguide, name="styleguide"),
    path("", include("apps.announcements.urls")),
    path("competency/", include("apps.competency.urls")),
    path("dashboards/", include("apps.dashboards.urls")),
    path("feedback/", include("apps.feedback.urls")),
    path("", include("apps.certificates.urls")),
    path("assessments/", include("apps.assessments.urls")),
    path("courses/", include("apps.courses.urls")),
    path("library/", include("apps.library.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("profiles/", include("apps.profiles.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.accounts.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
