"""Accounts — Clients, memberships, revocable API keys, and the mapping from passkey-backed smart accounts to studio clients.

Scaffolded in Phase 0 so the bounded context has a home and an import
path from the first commit. Models land in Phase 2:
Client, Membership, ApiKey, SmartAccount.

Every state change in this app is expected to append to the ledger via
apps.ledger.services.append_event rather than mutating silently.
"""
