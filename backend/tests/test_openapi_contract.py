"""The contract with the frontend.

The generated TypeScript client is derived from this schema, so these tests
guard the seam between the two runtimes: a rename that would break the Next app
fails here first.
"""

from __future__ import annotations

import pytest

from bbsbackend.api import api

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def schema():
    return api.get_openapi_schema()


def test_schema_is_openapi_31(schema):
    assert schema["openapi"].startswith("3.1")


def test_published_paths_are_stable(schema):
    """Adding paths is fine; removing or renaming these is a breaking change."""
    expected = {
        "/api/v1/system/health",
        "/api/v1/system/version",
        "/api/v1/ledger/head",
        "/api/v1/ledger/events",
        "/api/v1/ledger/events/{seq}",
        "/api/v1/ledger/verify",
        "/api/v1/ledger/anchors",
        "/api/v1/ledger/event-types",
    }
    assert expected <= set(schema["paths"])


def test_every_operation_has_an_explicit_stable_id(schema):
    """Generated operation ids are process-dependent.

    django-ninja falls back to a hashed suffix that changes between runs, which
    would churn the generated TypeScript client on every export and make the
    CI contract check meaningless. Every endpoint declares its own id.
    """
    import re

    for path, methods in schema["paths"].items():
        for method, operation in methods.items():
            operation_id = operation.get("operationId", "")
            assert operation_id, f"{method.upper()} {path} has no operationId"
            assert not re.search(r"_[0-9a-f]{8}$", operation_id), (
                f"{method.upper()} {path} uses a generated operationId "
                f"({operation_id}); pass operation_id= explicitly."
            )


def test_event_payload_exposes_the_fields_a_verifier_needs(schema):
    event = schema["components"]["schemas"]["EventOut"]["properties"]
    for field in ("seq", "uuid", "type", "occurred_at", "payload_hash", "prev_hash", "hash"):
        assert field in event, field


def test_append_endpoint_is_documented_as_a_write(schema):
    assert "post" in schema["paths"]["/api/v1/ledger/events"]
