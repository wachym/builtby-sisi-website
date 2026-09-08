"""Rails — Invoices, milestone escrow state, yield positions, and per-call API metering.

Scaffolded in Phase 0 so the bounded context has a home and an import
path from the first commit. Models land in Phase 3:
Invoice, EscrowState, YieldPosition, MeterUsage.

Every state change in this app is expected to append to the ledger via
apps.ledger.services.append_event rather than mutating silently.
"""
