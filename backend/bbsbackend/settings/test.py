"""Test settings: in-memory, deterministic, fast."""

from .dev import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

LEDGER_REQUIRE_SIGNATURES = False
INTERNAL_API_KEYS = ["test-internal-key"]

# Throttling is exercised by its own tests, not by every request in the suite.
NINJA_DEFAULT_THROTTLE_RATES = {"anon": "10000/min", "user": "10000/min"}
