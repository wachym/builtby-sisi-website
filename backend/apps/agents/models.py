"""Agents — Durable agent runs: steps, tool calls, human approvals, and per-agent budget ceilings.

Scaffolded in Phase 0 so the bounded context has a home and an import
path from the first commit. Models land in Phase 2:
AgentRun, Step, ToolCall, Approval, Budget.

Every state change in this app is expected to append to the ledger via
apps.ledger.services.append_event rather than mutating silently.
"""
