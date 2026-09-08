"""The append-only guarantee, tested at every layer that claims it.

If any of these start passing silently, the ledger's central promise is gone.
"""

from __future__ import annotations

import pytest
from django.db import DatabaseError, connection

from apps.ledger import services
from apps.ledger.exceptions import AppendOnlyViolation
from apps.ledger.models import Event

pytestmark = pytest.mark.django_db


def test_saving_an_existing_event_is_rejected():
    event = services.append_event(event_type="system.note", payload={"n": 1})
    event.subject = "tampered"
    with pytest.raises(AppendOnlyViolation):
        event.save()


def test_deleting_an_event_is_rejected():
    event = services.append_event(event_type="system.note", payload={"n": 1})
    with pytest.raises(AppendOnlyViolation):
        event.delete()


def test_queryset_update_is_rejected():
    services.append_event(event_type="system.note", payload={"n": 1})
    with pytest.raises(AppendOnlyViolation):
        Event.objects.all().update(subject="tampered")


def test_queryset_delete_is_rejected():
    services.append_event(event_type="system.note", payload={"n": 1})
    with pytest.raises(AppendOnlyViolation):
        Event.objects.all().delete()


def test_constructing_an_event_without_a_chain_is_rejected():
    """The service is the only door in."""
    from django.utils import timezone

    with pytest.raises(AppendOnlyViolation):
        Event(type="system.note", occurred_at=timezone.now(), payload={}).save()


def test_raw_sql_update_is_rejected_by_the_database():
    """The guard that survives code: a trigger, not a Python method."""
    event = services.append_event(event_type="system.note", payload={"n": 1})

    with pytest.raises(DatabaseError):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE ledger_event SET subject = %s WHERE seq = %s",
                ["tampered", event.seq],
            )


def test_raw_sql_delete_is_rejected_by_the_database():
    event = services.append_event(event_type="system.note", payload={"n": 1})

    with pytest.raises(DatabaseError):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM ledger_event WHERE seq = %s", [event.seq])

    assert Event.objects.filter(seq=event.seq).exists()
