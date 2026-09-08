"""Signing and its refusals."""

from __future__ import annotations

import pytest

from apps.ledger import services
from apps.ledger.exceptions import SignatureInvalid, SignatureRequired
from apps.ledger.models import ActorKey, ActorType
from apps.ledger.signers import Ed25519Signer, NullSigner, verify_signature

pytestmark = pytest.mark.django_db


def test_signed_event_verifies_against_the_actor_key():
    signer = Ed25519Signer.generate()
    actor = ActorKey.objects.create(
        handle="foreman",
        actor_type=ActorType.AGENT,
        public_key=signer.public_key_hex,
    )

    event = services.append_event(
        event_type="agent.run.started", actor=actor, payload={"run": 1}, signer=signer
    )

    assert event.signature
    verify_signature(
        public_key_hex_value=actor.public_key,
        message=event.signing_bytes(),
        signature_hex=event.signature,
    )
    assert services.verify_signatures() == []


def test_signing_for_another_actors_key_is_rejected():
    """An agent cannot sign as someone else."""
    actor_signer = Ed25519Signer.generate()
    impostor = Ed25519Signer.generate()
    actor = ActorKey.objects.create(
        handle="quartermaster",
        actor_type=ActorType.AGENT,
        public_key=actor_signer.public_key_hex,
    )

    with pytest.raises(SignatureInvalid):
        services.append_event(
            event_type="invoice.issued", actor=actor, payload={}, signer=impostor
        )


def test_required_signatures_reject_an_unsigned_append(settings):
    settings.LEDGER_REQUIRE_SIGNATURES = True
    with pytest.raises(SignatureRequired):
        services.append_event(
            event_type="system.note", payload={"n": 1}, signer=NullSigner()
        )


def test_unsigned_appends_are_allowed_when_signatures_are_not_required(settings):
    settings.LEDGER_REQUIRE_SIGNATURES = False
    event = services.append_event(event_type="system.note", payload={"n": 1})
    assert event.signature == ""


def test_verify_signatures_flags_a_key_that_does_not_match(settings):
    """A stored signature whose actor key was later replaced must be caught."""
    signer = Ed25519Signer.generate()
    actor = ActorKey.objects.create(
        handle="scout", actor_type=ActorType.AGENT, public_key=signer.public_key_hex
    )
    services.append_event(
        event_type="brief.drafted", actor=actor, payload={"lead": 1}, signer=signer
    )

    rotated = Ed25519Signer.generate()
    ActorKey.objects.filter(pk=actor.pk).update(public_key=rotated.public_key_hex)

    problems = services.verify_signatures()
    assert len(problems) == 1
    assert "does not verify" in problems[0].reason
