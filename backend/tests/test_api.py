"""The HTTP surface: routing, permissions, and the shape the frontend consumes."""

from __future__ import annotations

import json

import pytest

from apps.ledger import services

pytestmark = pytest.mark.django_db

API = "/api/v1"


def test_health_reports_ok(client):
    response = client.get(f"{API}/system/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["migrations_pending"] == 0


def test_version_reports_the_api_version(client, settings):
    response = client.get(f"{API}/system/version")
    assert response.status_code == 200
    assert response.json()["api_version"] == settings.API_VERSION


def test_head_of_an_empty_ledger(client):
    response = client.get(f"{API}/ledger/head")
    assert response.status_code == 200
    assert response.json() == {"seq": 0, "hash": "0" * 64, "event_count": 0}


def test_events_are_listed_newest_first(client):
    services.append_event(event_type="system.note", payload={"n": 1})
    latest = services.append_event(event_type="system.note", payload={"n": 2})

    response = client.get(f"{API}/ledger/events")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["results"][0]["seq"] == latest.seq
    assert body["results"][0]["hash"] == latest.hash


def test_events_can_be_filtered_by_type_and_subject(client):
    services.append_event(event_type="system.note", subject="a", payload={})
    services.append_event(event_type="human.approved", subject="b", payload={})

    by_type = client.get(f"{API}/ledger/events", {"type": "human.approved"}).json()
    assert by_type["count"] == 1
    assert by_type["results"][0]["type"] == "human.approved"

    by_subject = client.get(f"{API}/ledger/events", {"subject": "a"}).json()
    assert by_subject["count"] == 1


def test_single_event_exposes_everything_needed_to_verify_it(client):
    event = services.append_event(event_type="system.note", payload={"n": 1})

    body = client.get(f"{API}/ledger/events/{event.seq}").json()
    for field in ("uuid", "type", "subject", "occurred_at", "payload", "payload_hash", "prev_hash", "hash"):
        assert field in body


def test_verify_endpoint_reports_a_healthy_chain(client):
    for index in range(3):
        services.append_event(event_type="system.note", payload={"n": index})

    body = client.get(f"{API}/ledger/verify").json()
    assert body["ok"] is True
    assert body["checked"] == 3
    assert body["problems"] == []


def test_event_types_are_published(client):
    body = client.get(f"{API}/ledger/event-types").json()
    values = {item["value"] for item in body}
    assert {"perception.captured", "escrow.released", "anchor.created"} <= values


# --- writes ---------------------------------------------------------------


def _post(client, body, key=None):
    headers = {"headers": {"X-Internal-Key": key}} if key else {}
    return client.post(
        f"{API}/ledger/events",
        data=json.dumps(body),
        content_type="application/json",
        **headers,
    )


def test_append_requires_an_internal_key(client):
    response = _post(client, {"type": "system.note", "payload": {"n": 1}})
    assert response.status_code in (401, 403)


def test_append_rejects_a_wrong_key(client):
    response = _post(client, {"type": "system.note"}, key="not-the-key")
    assert response.status_code in (401, 403)


def test_append_with_a_valid_key_records_the_event(client, settings):
    response = _post(
        client,
        {"type": "system.note", "subject": "engagement:1", "payload": {"n": 1}},
        key=settings.INTERNAL_API_KEYS[0],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["seq"] == 1
    assert body["prev_hash"] == "0" * 64
    assert body["subject"] == "engagement:1"


def test_appended_events_chain_through_the_api(client, settings):
    key = settings.INTERNAL_API_KEYS[0]
    first = _post(client, {"type": "system.note", "payload": {"n": 1}}, key=key).json()
    second = _post(client, {"type": "system.note", "payload": {"n": 2}}, key=key).json()

    assert second["prev_hash"] == first["hash"]
    assert client.get(f"{API}/ledger/verify").json()["ok"] is True
