"""API composition root.

One NinjaExtraAPI instance, one place where controllers are registered. Apps
own their controllers; this module decides what is exposed and under which
version. Keeping registration central makes the public surface reviewable in a
single file.
"""

from __future__ import annotations

from django.conf import settings
from ninja_extra import NinjaExtraAPI

from apps.core.controllers import SystemController
from apps.ledger.controllers import LedgerController

api = NinjaExtraAPI(
    title="Sisi OS API",
    version=settings.API_VERSION,
    description=(
        "System of record for Sisi OS: the append-only delivery ledger and the "
        "services built on it. Perception, cognition, and settlement all write here."
    ),
    urls_namespace="api-v1",
    docs_url="/docs",
)

api.register_controllers(
    SystemController,
    LedgerController,
)
