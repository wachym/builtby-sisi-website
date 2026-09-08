"""ASGI entrypoint.

ASGI rather than WSGI is deliberate: async controllers and the telemetry
socket in Phase 4 both need it, and switching later is disruptive.

Run:  uvicorn bbsbackend.asgi:application --host 0.0.0.0 --port 8000
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bbsbackend.settings.dev")

application = get_asgi_application()
