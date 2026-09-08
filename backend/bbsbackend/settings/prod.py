"""Production settings.

Fails loudly at import time rather than serving traffic in a weak posture.
"""

from django.core.exceptions import ImproperlyConfigured

from . import env
from .base import *  # noqa: F401,F403
from .base import DATABASES, LEDGER_REQUIRE_SIGNATURES

DEBUG = False

SECRET_KEY = env.get("DJANGO_SECRET_KEY", required=True)
ALLOWED_HOSTS = env.get_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be set in production.")

if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    raise ImproperlyConfigured(
        "Refusing to run production on SQLite. Set DATABASE_URL to a postgres:// URL."
    )

if not LEDGER_REQUIRE_SIGNATURES:
    raise ImproperlyConfigured(
        "LEDGER_REQUIRE_SIGNATURES cannot be disabled in production: unsigned "
        "events would make the ledger unverifiable."
    )

# --- Mail ------------------------------------------------------------------
# Django 6 passes OPTIONS to the backend as keyword arguments. The console
# backend from base.py would silently swallow production mail, so SMTP is the
# default here and `check --deploy` enforces it.

MAILERS = {
    "default": {
        "BACKEND": env.get(
            "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
        ),
        "OPTIONS": {
            "host": env.get("EMAIL_HOST", "localhost"),
            "port": env.get_int("EMAIL_PORT", 587),
            "username": env.get("EMAIL_HOST_USER"),
            "password": env.get("EMAIL_HOST_PASSWORD"),
            "use_tls": env.get_bool("EMAIL_USE_TLS", True),
        },
    },
}

DEFAULT_FROM_EMAIL = env.get("DEFAULT_FROM_EMAIL", "no-reply@builtbysisi.com")
SERVER_EMAIL = env.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# --- Transport security ----------------------------------------------------
# The container host terminates TLS, so trust its forwarded protocol header.

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.get_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = env.get_int("SECURE_HSTS_SECONDS", 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"

# Persistent connections: the API is chatty and Postgres is not free to reach.
DATABASES["default"]["CONN_MAX_AGE"] = env.get_int("DATABASE_CONN_MAX_AGE", 60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
