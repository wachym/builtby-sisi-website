"""Vision — Model registry with signed manifests, server-side inference fallback, and perception artifacts.

Scaffolded in Phase 0 so the bounded context has a home and an import
path from the first commit. Models land in Phase 1:
ModelVersion, Artifact, ServerInference.

Every state change in this app is expected to append to the ledger via
apps.ledger.services.append_event rather than mutating silently.
"""
