"""Schemas for system endpoints.

Pydantic models are the single definition of every payload in the system: the
generated TypeScript client is derived from these, so a change here surfaces in
the frontend build rather than at runtime.
"""

from __future__ import annotations

from datetime import datetime

from ninja import Schema


class HealthOut(Schema):
    status: str
    database: str
    migrations_pending: int | None
    time: datetime


class VersionOut(Schema):
    service: str
    api_version: str
    commit: str | None
    environment: str
