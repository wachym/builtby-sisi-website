"""WSGI entrypoint.

Kept for tooling that expects it. The deployed process is ASGI — see asgi.py.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bbsbackend.settings.dev")

application = get_wsgi_application()
