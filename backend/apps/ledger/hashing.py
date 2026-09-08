"""Canonical serialisation and hashing.

Pure functions, no Django imports: the definition of "what a hash covers" is
the most important thing in this system to keep stable and testable. If this
module changes, previously anchored roots stop verifying — so treat it as
append-only too.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from datetime import timezone as dt_timezone
from typing import Any, Iterable

GENESIS_HASH = "0" * 64
HASH_HEX_LENGTH = 64


def canonical_json(value: Any) -> bytes:
    """Deterministic JSON: sorted keys, no insignificant whitespace, UTF-8.

    Two processes must produce byte-identical output for the same logical
    payload, or the chain becomes unverifiable across machines.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_fallback,
    ).encode("utf-8")


def _fallback(value: Any) -> str:
    if isinstance(value, datetime):
        return _iso(value)
    return str(value)


def _iso(moment: datetime) -> str:
    """UTC ISO-8601, always suffixed 'Z'.

    Normalised so an event hashed on a machine in one timezone verifies on a
    machine in another. Naive datetimes are read as UTC rather than rejected,
    because a hash function is the wrong place to raise on configuration.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt_timezone.utc)
    return moment.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_hash(payload: Any) -> str:
    return sha256_hex(canonical_json(payload))


def event_digest(
    *,
    uuid: str,
    event_type: str,
    subject: str,
    actor: str,
    occurred_at: datetime | str,
    payload_hash_hex: str,
    prev_hash: str,
) -> str:
    """The event hash: identity, classification, time, payload, and lineage.

    `seq` is deliberately excluded. Ordering is proven by the prev_hash
    linkage, which cannot be reordered without breaking every later event;
    including a database-assigned number would make the digest depend on
    insertion mechanics.
    """
    occurred = _iso(occurred_at) if isinstance(occurred_at, datetime) else str(occurred_at)
    return sha256_hex(
        canonical_json(
            {
                "uuid": uuid,
                "type": event_type,
                "subject": subject,
                "actor": actor,
                "occurred_at": occurred,
                "payload_hash": payload_hash_hex,
                "prev_hash": prev_hash,
            }
        )
    )


def merkle_root(leaf_hashes: Iterable[str]) -> str:
    """Binary Merkle root over hex leaves, duplicating the last odd node.

    Returns the genesis (all-zero) hash for an empty set so an anchor can be
    recorded for a quiet day without a special case at the call site.
    """
    level = [bytes.fromhex(h) for h in leaf_hashes]
    if not level:
        return GENESIS_HASH

    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [
            hashlib.sha256(level[i] + level[i + 1]).digest()
            for i in range(0, len(level), 2)
        ]
    return level[0].hex()
