"""Local development settings.

Convenient by design, and never used anywhere a real request can reach.
"""

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, SECRET_KEY  # noqa: F401

DEBUG = True

# A fixed insecure key so local sessions survive a restart. Production requires
# a real key from the environment and refuses to start without one.
if not SECRET_KEY:
    SECRET_KEY = "django-insecure-dev-only-do-not-use-outside-localhost"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

# Signing is optional locally so the ledger can be exercised without keys.
# `manage.py ledger_keygen` prints a keypair when you want the real path.
LEDGER_REQUIRE_SIGNATURES = False

# Accept a predictable internal key locally so the write endpoint is testable.
INTERNAL_API_KEYS = ["dev-internal-key"]
