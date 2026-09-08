"""Signing.

Ed25519, behind a narrow interface. The interface exists because production
must not sign with a key sitting in the application's memory: `Ed25519Signer`
is for local development and CI, and the signer service that replaces it in
Phase 5 implements the same two methods.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from django.conf import settings

from .exceptions import SignatureInvalid


@runtime_checkable
class Signer(Protocol):
    """Anything that can sign event bytes and name its public key."""

    @property
    def public_key_hex(self) -> str: ...

    def sign(self, message: bytes) -> str: ...


class NullSigner:
    """Signs nothing.

    Only usable where `LEDGER_REQUIRE_SIGNATURES` is False — local development
    and tests. Production settings refuse to start with signatures disabled.
    """

    @property
    def public_key_hex(self) -> str:
        return ""

    def sign(self, message: bytes) -> str:
        return ""


class Ed25519Signer:
    """Holds a private key in process. Development and CI only."""

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self._private_key = private_key

    @classmethod
    def generate(cls) -> "Ed25519Signer":
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_private_key_hex(cls, private_key_hex: str) -> "Ed25519Signer":
        return cls(Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex)))

    @property
    def private_key_hex(self) -> str:
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
        )

        return self._private_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption(),
        ).hex()

    @property
    def public_key_hex(self) -> str:
        return public_key_hex(self._private_key.public_key())

    def sign(self, message: bytes) -> str:
        return self._private_key.sign(message).hex()


def public_key_hex(public_key: Ed25519PublicKey) -> str:
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    return public_key.public_bytes(
        encoding=Encoding.Raw, format=PublicFormat.Raw
    ).hex()


def verify_signature(*, public_key_hex_value: str, message: bytes, signature_hex: str) -> None:
    """Raise SignatureInvalid unless the signature verifies."""
    if not public_key_hex_value or not signature_hex:
        raise SignatureInvalid("A public key and a signature are both required.")
    try:
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex_value))
        key.verify(bytes.fromhex(signature_hex), message)
    except (InvalidSignature, ValueError) as exc:
        raise SignatureInvalid("Signature does not verify for this actor.") from exc


def default_signer() -> Signer:
    """The signer configured for this environment.

    A key in `LEDGER_SIGNING_KEY` is used when present; otherwise signing is a
    no-op, which base settings only permit when signatures are not required.
    """
    key = getattr(settings, "LEDGER_SIGNING_KEY", "")
    if key:
        return Ed25519Signer.from_private_key_hex(key)
    return NullSigner()
