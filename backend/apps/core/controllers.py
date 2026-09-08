"""System endpoints: liveness, readiness, and deployed version.

Health is honest about degradation rather than returning 200 whatever happens:
a container host that cannot tell a broken database from a healthy one will
happily route traffic into an outage.
"""

import logging

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from ninja import Status
from ninja_extra import ControllerBase, api_controller, http_get
from ninja_extra.permissions import AllowAny

from .schemas import HealthOut, VersionOut

logger = logging.getLogger("sisi.core")


@api_controller("/system", tags=["system"], permissions=[AllowAny])
class SystemController(ControllerBase):
    @http_get(
        "/health",
        response={200: HealthOut, 503: HealthOut},
        url_name="health",
        operation_id="system_health",
    )
    def health(self):
        """Readiness probe: database reachable and schema up to date."""
        database = "ok"
        migrations_pending: int | None = None
        status = "ok"

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:  # pragma: no cover - exercised in outage, not in tests
            logger.exception("health check: database unreachable")
            database = "unreachable"
            status = "degraded"

        if database == "ok":
            try:
                executor = MigrationExecutor(connection)
                targets = executor.loader.graph.leaf_nodes()
                migrations_pending = len(executor.migration_plan(targets))
                if migrations_pending:
                    status = "degraded"
            except Exception:  # pragma: no cover - migration state is advisory
                logger.exception("health check: could not read migration state")
                migrations_pending = None

        payload = HealthOut(
            status=status,
            database=database,
            migrations_pending=migrations_pending,
            time=timezone.now(),
        )
        return Status(200 if status == "ok" else 503, payload)

    @http_get(
        "/version",
        response=VersionOut,
        url_name="version",
        operation_id="system_version",
    )
    def version(self):
        """What is actually deployed here."""
        return VersionOut(
            service="sisi-os-backend",
            api_version=settings.API_VERSION,
            commit=settings.GIT_COMMIT_SHA or None,
            environment=settings.SETTINGS_MODULE.rsplit(".", 1)[-1]
            if hasattr(settings, "SETTINGS_MODULE")
            else "unknown",
        )
