"""Ledger payload definitions.

These are the shapes the frontend receives. They are intentionally flat and
boring: a verifier written by someone who does not trust us should be able to
re-derive every hash from what is returned here.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from ninja import Field, Schema


class EventOut(Schema):
    seq: int
    uuid: UUID
    type: str
    subject: str
    actor: str | None
    occurred_at: datetime
    recorded_at: datetime
    payload: dict[str, Any]
    payload_hash: str
    prev_hash: str
    hash: str
    signature: str

    @staticmethod
    def resolve_actor(obj) -> str | None:
        """None means no actor, rather than an actor with an empty handle."""
        return obj.actor.handle if obj.actor_id else None


class EventIn(Schema):
    """An append request from an internal service."""

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    subject: str = ""
    actor: str | None = None
    occurred_at: datetime | None = None


class HeadOut(Schema):
    seq: int
    hash: str
    event_count: int


class ChainProblemOut(Schema):
    seq: int
    reason: str


class ChainReportOut(Schema):
    ok: bool
    checked: int
    head_seq: int
    head_hash: str
    problems: list[ChainProblemOut]


class AnchorOut(Schema):
    period: date
    first_seq: int
    last_seq: int
    event_count: int
    merkle_root: str
    head_hash: str
    chain: str
    tx_hash: str
    status: str
    anchored_at: datetime | None
    created_at: datetime


class EventTypeOut(Schema):
    value: str
    label: str
