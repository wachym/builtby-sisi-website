"""Intake — Inbound leads, qualified briefs, estimates, and milestone plans produced by the Scout and Cartographer agents.

Scaffolded in Phase 0 so the bounded context has a home and an import
path from the first commit. Models land in Phase 2:
Lead, Brief, Estimate, MilestonePlan.

Every state change in this app is expected to append to the ledger via
apps.ledger.services.append_event rather than mutating silently.
"""
