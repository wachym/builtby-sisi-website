"""Telemetry — Robot devices, streaming sessions, and the perception events that trigger the loop.

Scaffolded in Phase 0 so the bounded context has a home and an import
path from the first commit. Models land in Phase 4:
Device, Session, PerceptionEvent.

Every state change in this app is expected to append to the ledger via
apps.ledger.services.append_event rather than mutating silently.
"""
