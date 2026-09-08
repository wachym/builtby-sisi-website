"""Anchoring: a day of the ledger reduced to one root."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest

from apps.ledger import services
from apps.ledger.hashing import GENESIS_HASH, merkle_root
from apps.ledger.models import Anchor, Event

pytestmark = pytest.mark.django_db

DAY = datetime(2026, 9, 7, 10, 0, tzinfo=dt_timezone.utc)


def test_anchor_covers_only_its_own_day():
    inside = [
        services.append_event(
            event_type="system.note", payload={"n": n}, occurred_at=DAY
        )
        for n in range(3)
    ]
    services.append_event(
        event_type="system.note",
        payload={"n": "next day"},
        occurred_at=DAY.replace(day=8),
    )

    anchor = services.build_anchor(DAY.date())

    assert anchor.event_count == 3
    assert anchor.first_seq == inside[0].seq
    assert anchor.last_seq == inside[-1].seq
    assert anchor.merkle_root == merkle_root([event.hash for event in inside])


def test_anchor_records_itself_in_the_ledger():
    services.append_event(event_type="system.note", payload={}, occurred_at=DAY)
    services.build_anchor(DAY.date())

    recorded = Event.objects.filter(type="anchor.created").first()
    assert recorded is not None
    assert recorded.payload["period"] == DAY.date().isoformat()
    assert recorded.subject == f"anchor:{DAY.date().isoformat()}"


def test_anchoring_a_quiet_day_is_valid_and_appends_nothing():
    anchor = services.build_anchor(DAY.date())
    assert anchor.event_count == 0
    assert anchor.merkle_root == GENESIS_HASH
    assert not Event.objects.filter(type="anchor.created").exists()


def test_anchoring_twice_does_not_create_a_second_anchor():
    services.append_event(event_type="system.note", payload={}, occurred_at=DAY)
    first = services.build_anchor(DAY.date())
    second = services.build_anchor(DAY.date())

    assert first.pk == second.pk
    assert Anchor.objects.count() == 1


def test_a_submitted_anchor_is_never_rewritten():
    """Once a root is published, re-running the job must not change it."""
    services.append_event(event_type="system.note", payload={}, occurred_at=DAY)
    anchor = services.build_anchor(DAY.date())
    original_root = anchor.merkle_root
    anchor.mark_submitted(tx_hash="0xdeadbeef", chain="base-sepolia")

    services.append_event(event_type="system.note", payload={"late": True}, occurred_at=DAY)
    unchanged = services.build_anchor(DAY.date())

    assert unchanged.merkle_root == original_root
    assert unchanged.status == Anchor.Status.SUBMITTED
    assert unchanged.tx_hash == "0xdeadbeef"


def test_anchors_are_exposed_over_the_api(client):
    services.append_event(event_type="system.note", payload={}, occurred_at=DAY)
    services.build_anchor(DAY.date())

    body = client.get("/api/v1/ledger/anchors").json()
    assert len(body) == 1
    assert body[0]["period"] == DAY.date().isoformat()
    assert body[0]["status"] == "pending"
