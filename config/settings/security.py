"""Share environment-driven hardening defaults without mixing domain settings."""

import environ

env = environ.Env()
X_FRAME_OPTIONS = env("X_FRAME_OPTIONS", default="DENY")
SECURE_REFERRER_POLICY = env("SECURE_REFERRER_POLICY", default="same-origin")
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=12 * 60 * 60)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = env("SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SAMESITE = env("CSRF_COOKIE_SAMESITE", default="Lax")
USE_X_FORWARDED_PROTO = env.bool("USE_X_FORWARDED_PROTO", default=False)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if USE_X_FORWARDED_PROTO else None
)
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=0)
CONTENT_SECURITY_POLICY = env(
    "CONTENT_SECURITY_POLICY",
    default=(
        "default-src 'self'; frame-ancestors 'none'; "
        "base-uri 'self'; form-action 'self'"
    ),
)
ADMIN_URL = env("ADMIN_URL", default="django-admin/").strip("/") + "/"
LOGIN_FAILURE_LIMIT = env.int("LOGIN_FAILURE_LIMIT", default=5)
LOGIN_IP_LIMIT = env.int("LOGIN_IP_LIMIT", default=20)
LOGIN_WINDOW_SECONDS = env.int("LOGIN_WINDOW_SECONDS", default=15 * 60)
SIGNUP_IP_LIMIT = env.int("SIGNUP_IP_LIMIT", default=5)
SIGNUP_WINDOW_SECONDS = env.int("SIGNUP_WINDOW_SECONDS", default=60 * 60)
VERIFY_IP_LIMIT = env.int("VERIFY_IP_LIMIT", default=30)
VERIFY_WINDOW_SECONDS = env.int("VERIFY_WINDOW_SECONDS", default=60)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "capacity-connect",
    }
}
DEMO_PASSWORD = env("DEMO_PASSWORD", default="Demo-Connect-2026!")
