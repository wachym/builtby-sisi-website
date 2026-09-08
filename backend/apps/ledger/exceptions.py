"""Ledger errors.

Separate module so models, services, and signers can raise the same types
without importing each other.
"""


class LedgerError(Exception):
    """Base class for every ledger failure."""


class AppendOnlyViolation(LedgerError):
    """Something tried to modify or delete a recorded event."""


class SignatureRequired(LedgerError):
    """Signatures are mandatory in this environment and none was supplied."""


class SignatureInvalid(LedgerError):
    """A signature was supplied but does not verify against the actor's key."""


class ChainBroken(LedgerError):
    """The hash chain does not verify."""
