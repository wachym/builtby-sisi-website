"""Chain construction and verification."""

from __future__ import annotations

import pytest

from apps.ledger import services
from apps.ledger.hashing import GENESIS_HASH, payload_hash
from apps.ledger.models import ActorKey, ActorType, Event

pytestmark = pytest.mark.django_db


def test_first_event_links_to_genesis():
    event = services.append_event(event_type="system.note", payload={"note": "first"})
    assert event.prev_hash == GENESIS_HASH
    assert event.seq == 1
    assert event.hash == event.compute_hash()


def test_events_link_to_their_predecessor():
    first = services.append_event(event_type="system.note", payload={"n": 1})
    second = services.append_event(event_type="system.note", payload={"n": 2})
    third = services.append_event(event_type="system.note", payload={"n": 3})

    assert second.prev_hash == first.hash
    assert third.prev_hash == second.hash
    assert len({first.hash, second.hash, third.hash}) == 3


def test_head_reflects_the_newest_event():
    assert services.head() == (0, GENESIS_HASH)
    services.append_event(event_type="system.note", payload={"n": 1})
    latest = services.append_event(event_type="system.note", payload={"n": 2})
    assert services.head() == (latest.seq, latest.hash)


def test_verify_chain_accepts_a_well_formed_chain():
    for index in range(5):
        services.append_event(
            event_type="perception.captured",
            subject=f"device:{index % 2}",
            payload={"index": index},
        )

    report = services.verify_chain()
    assert report.ok
    assert report.checked == 5
    assert report.problems == []


def test_append_records_the_actor_and_hashes_its_handle():
    actor = ActorKey.objects.create(handle="foreman", actor_type=ActorType.AGENT)
    event = services.append_event(
        event_type="agent.run.started", actor=actor, payload={"run": 1}
    )
    assert event.actor_handle == "foreman"

    # The actor is part of the digest: the same event by a different actor is
    # a different fact.
    other = ActorKey.objects.create(handle="scout", actor_type=ActorType.AGENT)
    event.actor = other
    assert event.compute_hash() != event.hash


def test_actor_may_be_referenced_by_handle():
    ActorKey.objects.create(handle="sentinel", actor_type=ActorType.AGENT)
    event = services.append_event(event_type="system.note", actor="sentinel", payload={})
    assert event.actor_handle == "sentinel"


def test_payload_hash_covers_the_payload():
    payload = {"amount": "1000.00", "currency": "USDC"}
    event = services.append_event(event_type="invoice.issued", payload=payload)
    assert event.payload_hash == payload_hash(payload)


# --- verification of broken chains ---------------------------------------
# The database refuses to let us corrupt a stored chain, which is the point.
# The negative paths are therefore exercised against the pure verifier.


def _row(seq, prev_hash, *, uuid="0f9d5f3a-0000-4000-8000-00000000000{}", **overrides):
    from datetime import datetime
    from datetime import timezone as dt_timezone

    from apps.ledger.hashing import event_digest

    payload = overrides.pop("payload", {"n": seq})
    occurred_at = datetime(2026, 9, 8, 12, seq, tzinfo=dt_timezone.utc)
    row = {
        "seq": seq,
        "uuid": uuid.format(seq),
        "type": "system.note",
        "subject": "",
        "actor_handle": "",
        "occurred_at": occurred_at,
        "payload": payload,
        "payload_hash": payload_hash(payload),
        "prev_hash": prev_hash,
    }
    row["hash"] = event_digest(
        uuid=row["uuid"],
        event_type=row["type"],
        subject=row["subject"],
        actor=row["actor_handle"],
        occurred_at=occurred_at,
        payload_hash_hex=row["payload_hash"],
        prev_hash=prev_hash,
    )
    row.update(overrides)
    return row


def test_verify_rows_detects_a_broken_link():
    first = _row(1, GENESIS_HASH)
    second = _row(2, "9" * 64)  # points at nothing

    report = services.verify_rows([first, second])
    assert not report.ok
    assert any("prev_hash" in problem.reason for problem in report.problems)


def test_verify_rows_detects_a_tampered_payload():
    first = _row(1, GENESIS_HASH)
    tampered = dict(first)
    tampered["payload"] = {"n": "edited after the fact"}

    report = services.verify_rows([tampered])
    assert not report.ok
    assert any("payload" in problem.reason for problem in report.problems)


def test_verify_rows_detects_a_forged_hash():
    first = _row(1, GENESIS_HASH)
    forged = dict(first)
    forged["hash"] = "f" * 64

    report = services.verify_rows([forged])
    assert not report.ok
    assert any("hash" in problem.reason for problem in report.problems)


def test_verify_rows_detects_a_reordered_chain():
    first = _row(1, GENESIS_HASH)
    second = _row(2, first["hash"])

    report = services.verify_rows([second, first])
    assert not report.ok
