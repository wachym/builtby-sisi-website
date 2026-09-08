"""Ledger services — the only sanctioned way to write to the spine.

Two invariants are defended here:

1. **Serialised appends.** Two concurrent writers must not read the same
   `prev_hash`. On PostgreSQL a transaction-scoped advisory lock serialises
   appends; on SQLite the database's own write lock does the same job.
2. **Nothing unverifiable.** When the environment requires signatures, an
   append without a valid one fails rather than recording a fact nobody can
   check later.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable, Sequence

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from .exceptions import SignatureRequired
from .hashing import GENESIS_HASH, event_digest, merkle_root, payload_hash
from .models import ActorKey, Anchor, Event
from .signers import Signer, default_signer, verify_signature

logger = logging.getLogger("sisi.ledger")

# Arbitrary but fixed: the advisory lock identifying the append chain.
CHAIN_LOCK_ID = 0x5151_0001


def _lock_chain() -> None:
    """Serialise appends across processes.

    PostgreSQL: a transaction-scoped advisory lock, released at commit.
    SQLite: no-op — its write transactions already serialise, and the lock
    would be meaningless in a single-writer database.
    """
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CHAIN_LOCK_ID])


def head() -> tuple[int, str]:
    """(seq, hash) of the newest event, or (0, genesis) for an empty ledger."""
    last = Event.objects.order_by("-seq").values("seq", "hash").first()
    if not last:
        return 0, GENESIS_HASH
    return last["seq"], last["hash"]


@transaction.atomic
def append_event(
    *,
    event_type: str,
    payload: dict[str, Any] | None = None,
    subject: str = "",
    actor: ActorKey | str | None = None,
    occurred_at: datetime | None = None,
    signer: Signer | None = None,
) -> Event:
    """Record one fact and return it.

    `actor` accepts an ActorKey or a handle. When signatures are required, the
    actor must have a registered public key and the signer must match it.
    """
    _lock_chain()

    actor_obj = _resolve_actor(actor)
    payload = payload or {}
    occurred = occurred_at or timezone.now()

    last = Event.objects.select_for_update().order_by("-seq").first()
    prev_hash = last.hash if last else GENESIS_HASH

    event = Event(
        type=event_type,
        subject=subject,
        actor=actor_obj,
        occurred_at=occurred,
        payload=payload,
        payload_hash=payload_hash(payload),
        prev_hash=prev_hash,
    )
    event.hash = event.compute_hash()

    signer = signer or default_signer()
    signature = signer.sign(event.signing_bytes())

    require = getattr(settings, "LEDGER_REQUIRE_SIGNATURES", True)
    if require and not signature:
        raise SignatureRequired(
            "LEDGER_REQUIRE_SIGNATURES is on but no signer is configured. Set "
            "LEDGER_SIGNING_KEY or pass an explicit signer."
        )

    if signature:
        expected_key = (
            actor_obj.public_key
            if actor_obj and actor_obj.public_key
            else signer.public_key_hex
        )
        # Verify what we are about to store: a signature that does not check
        # out is worse than none, because it implies verification happened.
        verify_signature(
            public_key_hex_value=expected_key,
            message=event.signing_bytes(),
            signature_hex=signature,
        )
        event.signature = signature

    event.save()
    logger.info(
        "ledger append seq=%s type=%s subject=%s actor=%s",
        event.seq,
        event.type,
        event.subject or "-",
        event.actor_handle or "-",
    )
    return event


def _resolve_actor(actor: ActorKey | str | None) -> ActorKey | None:
    if actor is None or isinstance(actor, ActorKey):
        return actor
    return ActorKey.objects.filter(handle=actor, is_active=True).first()


# --- verification ---------------------------------------------------------


@dataclass(frozen=True)
class ChainProblem:
    seq: int
    reason: str


@dataclass
class ChainReport:
    ok: bool
    checked: int
    head_seq: int
    head_hash: str
    problems: list[ChainProblem] = field(default_factory=list)


def verify_rows(rows: Sequence[dict[str, Any]], *, start_hash: str = GENESIS_HASH) -> ChainReport:
    """Verify an ordered sequence of event rows.

    A pure function over dictionaries, so the negative paths are testable
    without having to defeat the database's own append-only guards.
    """
    problems: list[ChainProblem] = []
    expected_prev = start_hash
    last_seq = 0
    last_hash = start_hash

    for row in rows:
        seq = row["seq"]
        if row["prev_hash"] != expected_prev:
            problems.append(
                ChainProblem(seq=seq, reason="prev_hash does not match the previous event")
            )
        if payload_hash(row["payload"]) != row["payload_hash"]:
            problems.append(ChainProblem(seq=seq, reason="payload does not match payload_hash"))

        recomputed = event_digest(
            uuid=str(row["uuid"]),
            event_type=row["type"],
            subject=row["subject"],
            actor=row.get("actor_handle") or "",
            occurred_at=row["occurred_at"],
            payload_hash_hex=row["payload_hash"],
            prev_hash=row["prev_hash"],
        )
        if recomputed != row["hash"]:
            problems.append(ChainProblem(seq=seq, reason="hash does not match event contents"))

        expected_prev = row["hash"]
        last_seq, last_hash = seq, row["hash"]

    return ChainReport(
        ok=not problems,
        checked=len(rows),
        head_seq=last_seq,
        head_hash=last_hash,
        problems=problems,
    )


def verify_chain(*, since_seq: int = 0, limit: int | None = None) -> ChainReport:
    """Verify the recorded chain, oldest first."""
    queryset = (
        Event.objects.filter(seq__gt=since_seq)
        .select_related("actor")
        .order_by("seq")
    )
    if limit:
        queryset = queryset[:limit]

    rows = [
        {
            "seq": event.seq,
            "uuid": event.uuid,
            "type": event.type,
            "subject": event.subject,
            "actor_handle": event.actor_handle,
            "occurred_at": event.occurred_at,
            "payload": event.payload,
            "payload_hash": event.payload_hash,
            "prev_hash": event.prev_hash,
            "hash": event.hash,
        }
        for event in queryset
    ]

    start_hash = GENESIS_HASH
    if since_seq:
        previous = Event.objects.filter(seq__lte=since_seq).order_by("-seq").first()
        if previous:
            start_hash = previous.hash

    return verify_rows(rows, start_hash=start_hash)


def verify_signatures(*, since_seq: int = 0) -> list[ChainProblem]:
    """Check every stored signature against its actor's registered key."""
    problems: list[ChainProblem] = []
    for event in (
        Event.objects.filter(seq__gt=since_seq)
        .exclude(signature="")
        .select_related("actor")
        .order_by("seq")
    ):
        key = event.actor.public_key if event.actor_id else ""
        try:
            verify_signature(
                public_key_hex_value=key,
                message=event.signing_bytes(),
                signature_hex=event.signature,
            )
        except Exception as exc:  # SignatureInvalid, or a malformed key
            problems.append(ChainProblem(seq=event.seq, reason=str(exc)))
    return problems


# --- anchoring ------------------------------------------------------------


def build_anchor(period: date, *, chain: str | None = None) -> Anchor:
    """Reduce one UTC day of events to a Merkle root and record it.

    Idempotent: anchoring the same day twice updates the pending root rather
    than creating a second one. An already-submitted anchor is left alone —
    rewriting a published root is exactly the thing this system exists to
    prevent.
    """
    events = list(
        Event.objects.filter(occurred_at__date=period)
        .order_by("seq")
        .values_list("seq", "hash")
    )
    root = merkle_root([h for _, h in events])
    head_seq, head_hash = head()

    existing = Anchor.objects.filter(period=period).first()
    if existing and existing.status != Anchor.Status.PENDING:
        logger.warning(
            "anchor for %s is already %s; leaving it untouched", period, existing.status
        )
        return existing

    defaults = {
        "first_seq": events[0][0] if events else 0,
        "last_seq": events[-1][0] if events else 0,
        "event_count": len(events),
        "merkle_root": root,
        "head_hash": head_hash,
        "chain": chain or getattr(settings, "LEDGER_ANCHOR_CHAIN", ""),
        "status": Anchor.Status.PENDING,
    }
    anchor, created = Anchor.objects.update_or_create(period=period, defaults=defaults)

    # The anchor is itself a fact, so it belongs in the ledger — but only when
    # it covers something, otherwise a quiet day would append noise forever.
    if created and events:
        append_event(
            event_type="anchor.created",
            subject=f"anchor:{period.isoformat()}",
            payload={
                "period": period.isoformat(),
                "merkle_root": root,
                "event_count": len(events),
                "first_seq": defaults["first_seq"],
                "last_seq": defaults["last_seq"],
                "head_seq": head_seq,
            },
        )
    return anchor


def event_types() -> Iterable[str]:
    from .models import EventType

    return [choice.value for choice in EventType]
