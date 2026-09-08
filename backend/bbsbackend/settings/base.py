"""Settings shared by every environment.

Nothing here is unsafe by default: DEBUG is off, hosts are empty, and secrets
come from the environment. Development relaxes those in dev.py; production
tightens them further in prod.py.
"""

from __future__ import annotations

from pathlib import Path

from . import env

# backend/bbsbackend/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parents[2]

env.load_dotenv(BASE_DIR / ".env")

# --- Core ------------------------------------------------------------------

SECRET_KEY = env.get("DJANGO_SECRET_KEY")
DEBUG = env.get_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env.get_list("DJANGO_ALLOWED_HOSTS")

ROOT_URLCONF = "bbsbackend.urls"
WSGI_APPLICATION = "bbsbackend.wsgi.application"
ASGI_APPLICATION = "bbsbackend.asgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Applications ----------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "ninja_extra",
    "corsheaders",
]

# The planes of Sisi OS. Each app owns one bounded context; controllers are
# registered centrally in bbsbackend/api.py.
LOCAL_APPS = [
    "apps.core",       # health, version, OpenAPI export, shared primitives
    "apps.ledger",     # append-only event chain, anchoring, verification
    "apps.accounts",   # clients, API keys, smart-account mapping
    "apps.intake",     # leads, briefs, estimates, milestone plans
    "apps.vision",     # model registry, server inference, artifacts
    "apps.agents",     # runs, steps, tool calls, approvals, budgets
    "apps.telemetry",  # devices, sessions, perception events
    "apps.rails",      # invoices, escrow state, yield, metering
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware must precede CommonMiddleware so preflight requests are
    # answered before any redirect logic runs.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database --------------------------------------------------------------

DATABASES = {
    "default": env.database_from_url(
        env.get("DATABASE_URL", "sqlite:///db.sqlite3"),
        BASE_DIR,
        conn_max_age=env.get_int("DATABASE_CONN_MAX_AGE", 0),
    )
}

# --- Auth ------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation --------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files ----------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Email (Django 6 mailer configuration) ---------------------------------

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# --- Cross-origin ----------------------------------------------------------
# The API is served from a subdomain of the app so session cookies stay
# first-party. Origins are allow-listed explicitly; wildcards are never used.

CORS_ALLOWED_ORIGINS = env.get_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.get_list("CSRF_TRUSTED_ORIGINS")

# --- API -------------------------------------------------------------------

API_VERSION = "1.0.0"
API_PREFIX = "api/v1/"

# Throttle rates consumed by ninja-extra. Metering in Phase 3 extends this
# mechanism rather than adding a second one.
NINJA_DEFAULT_THROTTLE_RATES = {
    "anon": env.get("THROTTLE_ANON_RATE", "120/min"),
    "user": env.get("THROTTLE_USER_RATE", "1000/min"),
}
NINJA_PAGINATION_PER_PAGE = 50
NINJA_PAGINATION_MAX_PER_PAGE_SIZE = 200

# Keys accepted in the X-Internal-Key header for privileged writes.
# Replaced by real, revocable keys owned by the accounts app in Phase 2.
INTERNAL_API_KEYS = env.get_list("INTERNAL_API_KEYS")

# --- Ledger ----------------------------------------------------------------

LEDGER_REQUIRE_SIGNATURES = env.get_bool("LEDGER_REQUIRE_SIGNATURES", True)
LEDGER_SIGNING_KEY = env.get("LEDGER_SIGNING_KEY")
LEDGER_SIGNING_ACTOR = env.get("LEDGER_SIGNING_ACTOR", "system")
LEDGER_ANCHOR_CHAIN = env.get("LEDGER_ANCHOR_CHAIN", "base-sepolia")

# --- Build metadata --------------------------------------------------------

GIT_COMMIT_SHA = env.get("GIT_COMMIT_SHA") or env.get("VERCEL_GIT_COMMIT_SHA")

# --- Logging ---------------------------------------------------------------

LOG_LEVEL = env.get("DJANGO_LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "sisi": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}
