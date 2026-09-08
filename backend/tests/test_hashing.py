"""Hashing is the foundation of every claim this system makes.

These tests pin the byte-level behaviour: if canonicalisation changes, every
previously anchored root stops verifying, so a failure here is a signal to
version the ledger rather than to update the expectation.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from apps.ledger.hashing import (
    GENESIS_HASH,
    canonical_json,
    event_digest,
    merkle_root,
    payload_hash,
)


def test_canonical_json_is_key_order_independent():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})


def test_canonical_json_has_no_insignificant_whitespace():
    assert canonical_json({"a": 1, "b": [1, 2]}) == b'{"a":1,"b":[1,2]}'


def test_payload_hash_matches_sha256_of_canonical_form():
    payload = {"z": True, "a": [3, 2, 1]}
    expected = hashlib.sha256(canonical_json(payload)).hexdigest()
    assert payload_hash(payload) == expected


def test_event_digest_is_timezone_normalised():
    """The same instant expressed in two zones must hash identically."""
    utc = datetime(2026, 9, 8, 12, 0, tzinfo=dt_timezone.utc)
    plus_three = utc.astimezone(dt_timezone(timedelta(hours=3)))

    common = dict(
        uuid="0f9d5f3a-0000-4000-8000-000000000001",
        event_type="system.note",
        subject="engagement:1",
        actor="system",
        payload_hash_hex=payload_hash({"note": "hello"}),
        prev_hash=GENESIS_HASH,
    )
    assert event_digest(occurred_at=utc, **common) == event_digest(
        occurred_at=plus_three, **common
    )


def test_event_digest_changes_when_any_field_changes():
    common = dict(
        uuid="0f9d5f3a-0000-4000-8000-000000000001",
        event_type="system.note",
        subject="engagement:1",
        actor="system",
        occurred_at=datetime(2026, 9, 8, 12, 0, tzinfo=dt_timezone.utc),
        payload_hash_hex=payload_hash({"note": "hello"}),
        prev_hash=GENESIS_HASH,
    )
    baseline = event_digest(**common)

    for field, value in [
        ("subject", "engagement:2"),
        ("actor", "someone-else"),
        ("event_type", "human.approved"),
        ("prev_hash", "1" * 64),
    ]:
        assert event_digest(**{**common, field: value}) != baseline, field


def test_merkle_root_of_empty_set_is_genesis():
    assert merkle_root([]) == GENESIS_HASH


def test_merkle_root_of_single_leaf_is_that_leaf():
    leaf = "aa" * 32
    assert merkle_root([leaf]) == leaf


def test_merkle_root_of_two_leaves():
    a, b = "aa" * 32, "bb" * 32
    expected = hashlib.sha256(bytes.fromhex(a) + bytes.fromhex(b)).hexdigest()
    assert merkle_root([a, b]) == expected


def test_merkle_root_duplicates_last_leaf_when_odd():
    a, b, c = "aa" * 32, "bb" * 32, "cc" * 32
    left = hashlib.sha256(bytes.fromhex(a) + bytes.fromhex(b)).digest()
    right = hashlib.sha256(bytes.fromhex(c) + bytes.fromhex(c)).digest()
    assert merkle_root([a, b, c]) == hashlib.sha256(left + right).hexdigest()


def test_merkle_root_is_order_sensitive():
    a, b = "aa" * 32, "bb" * 32
    assert merkle_root([a, b]) != merkle_root([b, a])
