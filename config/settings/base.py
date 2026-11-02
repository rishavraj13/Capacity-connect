"""Base settings shared across all execution environments."""

from pathlib import Path

import environ

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
env_file_path: Path = BASE_DIR / ".env"
if env_file_path.is_file():
    environ.Env.read_env(env_file_path)

SECRET_KEY: str = env("SECRET_KEY")
DEBUG: bool = env("DEBUG")
ALLOWED_HOSTS: list[str] = env("ALLOWED_HOSTS")

DJANGO_APPS: list[str] = [
    "config.admin_site_config.CapacityAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS: list[str] = []

LOCAL_APPS: list[str] = [
    "apps.core",
    "apps.accounts",
    "apps.catalog.apps.CatalogConfig",
    "apps.profiles.apps.ProfilesConfig",
    "apps.courses.apps.CoursesConfig",
    "apps.library.apps.LibraryConfig",
    "apps.assessments.apps.AssessmentsConfig",
    "apps.feedback.apps.FeedbackConfig",
    "apps.certificates.apps.CertificatesConfig",
    "apps.competency.apps.CompetencyConfig",
    "apps.announcements.apps.AnnouncementsConfig",
    "apps.dashboards.apps.DashboardsConfig",
]

INSTALLED_APPS: list[str] = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF: str = "config.urls"

TEMPLATES: list[dict] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION: str = "config.wsgi.application"
ASGI_APPLICATION: str = "config.asgi.application"

DATABASES: dict = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL: str = "accounts.User"

LANGUAGE_CODE: str = "en-us"
TIME_ZONE: str = "Asia/Kolkata"
USE_I18N: bool = True
USE_TZ: bool = True

STATIC_URL: str = "static/"
STATIC_ROOT: Path = BASE_DIR / "staticfiles"

MEDIA_URL: str = "media/"
MEDIA_ROOT: Path = BASE_DIR / "media"
PRIVATE_MEDIA_ROOT: Path = Path(
    env("PRIVATE_MEDIA_ROOT", default=str(BASE_DIR / "private_uploads"))
)

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

LOGIN_URL: str = "login"
LOGOUT_REDIRECT_URL: str = "login"

PHOTO_EXTENSIONS = ("jpg", "jpeg", "png")
CERTIFICATE_EXTENSIONS = ("pdf", *PHOTO_EXTENSIONS)
PHOTO_MAX_BYTES = env.int("PHOTO_MAX_BYTES", default=2 * 1024 * 1024)
CERTIFICATE_MAX_BYTES = env.int("CERTIFICATE_MAX_BYTES", default=5 * 1024 * 1024)


LIBRARY_EXTENSIONS = ("mp4", "webm", "pptx", "pdf", "docx")
LIBRARY_UPLOAD_EXTENSIONS = {
    "VIDEO": ("mp4", "webm"),
    "PRESENTATION": ("pptx", "pdf"),
    "DOCUMENT": ("pdf", "docx"),
}
LIBRARY_UPLOAD_LIMITS = {
    "VIDEO": env.int("LIBRARY_VIDEO_MAX_BYTES", default=200 * 1024 * 1024),
    "PRESENTATION": env.int("LIBRARY_PRESENTATION_MAX_BYTES", default=25 * 1024 * 1024),
    "DOCUMENT": env.int("LIBRARY_DOCUMENT_MAX_BYTES", default=25 * 1024 * 1024),
}

SITE_BASE_URL: str = env("SITE_BASE_URL", default="http://127.0.0.1:8000")
CERTIFICATE_SIGNATORY_NAME: str = env(
    "CERTIFICATE_SIGNATORY_NAME", default="Capacity Connect Administrator"
)
CERTIFICATE_SIGNATORY_TITLE: str = env(
    "CERTIFICATE_SIGNATORY_TITLE", default="Programme Director"
)

from config.settings.security import *  # noqa: F403, E402
