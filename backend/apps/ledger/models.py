"""The spine: an append-only, hash-chained event log.

Every meaningful act in the studio — a perception, a decision, an approval, a
settlement — is one row here, signed by its actor and linked to its
predecessor. Nothing in the system mutates history; it appends to it.

Enforcement is deliberately belt-and-braces:

* Python:   `save()` refuses updates, `delete()` refuses, and the default
            queryset refuses bulk `update()`/`delete()`.
* Database: triggers reject UPDATE and DELETE on the events table, so raw SQL
            and a future careless migration are covered too.

Use `apps.ledger.services.append_event()` to write. Constructing an Event by
hand is rejected, because a row without a computed chain is worse than no row.
"""

from __future__ import annotations

import uuid as uuid_lib

from django.db import models
from django.utils import timezone

from .exceptions import AppendOnlyViolation
from .hashing import GENESIS_HASH, HASH_HEX_LENGTH, event_digest


class ActorType(models.TextChoices):
    HUMAN = "human", "Human"
    AGENT = "agent", "Agent"
    DEVICE = "device", "Device"
    SYSTEM = "system", "System"


class EventType(models.TextChoices):
    """The vocabulary of the loop.

    Additive only: renaming a value would invalidate the digests of every
    event already recorded with it.
    """

    # Perception
    PERCEPTION_CAPTURED = "perception.captured", "Perception captured"
    ARTIFACT_STORED = "artifact.stored", "Artifact stored"
    # Cognition
    BRIEF_DRAFTED = "brief.drafted", "Brief drafted"
    ESTIMATE_PROPOSED = "estimate.proposed", "Estimate proposed"
    AGENT_RUN_STARTED = "agent.run.started", "Agent run started"
    AGENT_TOOL_CALLED = "agent.tool.called", "Agent tool called"
    AGENT_RUN_FINISHED = "agent.run.finished", "Agent run finished"
    HUMAN_APPROVED = "human.approved", "Human approved"
    HUMAN_REJECTED = "human.rejected", "Human rejected"
    # Delivery
    COMMIT_PUSHED = "commit.pushed", "Commit pushed"
    MILESTONE_DELIVERED = "milestone.delivered", "Milestone delivered"
    CLIENT_ACCEPTED = "client.accepted", "Client accepted"
    # Settlement
    INVOICE_ISSUED = "invoice.issued", "Invoice issued"
    ESCROW_FUNDED = "escrow.funded", "Escrow funded"
    ESCROW_RELEASED = "escrow.released", "Escrow released"
    YIELD_ACCRUED = "yield.accrued", "Yield accrued"
    # Spine
    ANCHOR_CREATED = "anchor.created", "Anchor created"
    SYSTEM_NOTE = "system.note", "System note"


class ActorKey(models.Model):
    """A signing identity: a person, an agent, a device, or the system itself.

    Public keys only. Private keys live with the actor — in a person's
    authenticator, on a device, or in the signer service — never here.
    """

    id = models.UUIDField(primary_key=True, default=uuid_lib.uuid4, editable=False)
    handle = models.SlugField(max_length=64, unique=True)
    actor_type = models.CharField(max_length=16, choices=ActorType.choices)
    public_key = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Ed25519 public key, 32 bytes hex-encoded.",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ledger_actor_key"
        ordering = ["handle"]
        verbose_name = "actor key"
        verbose_name_plural = "actor keys"

    def __str__(self) -> str:
        return f"{self.handle} ({self.actor_type})"


class AppendOnlyQuerySet(models.QuerySet):
    """Removes the bulk escape hatches around `save()`."""

    def update(self, **kwargs):
        raise AppendOnlyViolation(
            "The ledger is append-only: events cannot be updated. Append a "
            "correcting event instead."
        )

    def delete(self):
        raise AppendOnlyViolation(
            "The ledger is append-only: events cannot be deleted."
        )


class Event(models.Model):
    """One recorded fact.

    `seq` gives cheap ordering and pagination; `prev_hash` is what actually
    proves order. A row's `hash` covers its identity, type, subject, actor,
    event time, payload hash, and the hash before it.
    """

    seq = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)

    type = models.CharField(max_length=64, choices=EventType.choices, db_index=True)
    subject = models.CharField(
        max_length=200,
        blank=True,
        default="",
        db_index=True,
        help_text="What this is about, e.g. 'engagement:42' or 'milestone:7'.",
    )
    actor = models.ForeignKey(
        ActorKey,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="events",
    )

    occurred_at = models.DateTimeField(
        db_index=True, help_text="When the fact happened."
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True, help_text="When the ledger learned of it."
    )

    payload = models.JSONField(default=dict, blank=True)
    payload_hash = models.CharField(max_length=HASH_HEX_LENGTH)
    prev_hash = models.CharField(max_length=HASH_HEX_LENGTH)
    hash = models.CharField(max_length=HASH_HEX_LENGTH, unique=True)
    signature = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="Ed25519 signature over the event hash, 64 bytes hex-encoded.",
    )

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        db_table = "ledger_event"
        ordering = ["seq"]
        indexes = [
            models.Index(fields=["type", "occurred_at"], name="ledger_type_time_idx"),
            models.Index(fields=["subject", "seq"], name="ledger_subject_seq_idx"),
        ]

    def __str__(self) -> str:
        return f"#{self.seq} {self.type} {self.hash[:12]}"

    # --- append-only guards ------------------------------------------------

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AppendOnlyViolation(
                f"Event #{self.pk} is already recorded and cannot be modified. "
                "Append a correcting event instead."
            )
        if not self.hash or not self.payload_hash or not self.prev_hash:
            raise AppendOnlyViolation(
                "Events must be created through apps.ledger.services.append_event(), "
                "which computes the chain."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyViolation(
            f"Event #{self.pk} cannot be deleted: the ledger is append-only."
        )

    # --- integrity --------------------------------------------------------

    @property
    def actor_handle(self) -> str:
        return self.actor.handle if self.actor_id else ""

    def compute_hash(self, prev_hash: str | None = None) -> str:
        """Recompute this event's hash from its own fields."""
        return event_digest(
            uuid=str(self.uuid),
            event_type=self.type,
            subject=self.subject,
            actor=self.actor_handle,
            occurred_at=self.occurred_at,
            payload_hash_hex=self.payload_hash,
            prev_hash=self.prev_hash if prev_hash is None else prev_hash,
        )

    def signing_bytes(self) -> bytes:
        """What a signature covers: the event hash, as bytes."""
        return bytes.fromhex(self.hash)


class Anchor(models.Model):
    """A day of the ledger, reduced to one Merkle root.

    Publishing the root on-chain is what makes the studio's delivery history
    checkable by someone who does not trust the studio.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUBMITTED = "submitted", "Submitted"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"

    period = models.DateField(unique=True, help_text="UTC date covered.")
    first_seq = models.BigIntegerField()
    last_seq = models.BigIntegerField()
    event_count = models.PositiveIntegerField()
    merkle_root = models.CharField(max_length=HASH_HEX_LENGTH)
    head_hash = models.CharField(
        max_length=HASH_HEX_LENGTH,
        default=GENESIS_HASH,
        help_text="Chain head at the moment of anchoring.",
    )

    chain = models.CharField(max_length=32, blank=True, default="")
    tx_hash = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    anchored_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_anchor"
        ordering = ["-period"]

    def __str__(self) -> str:
        return f"{self.period} {self.merkle_root[:12]} ({self.status})"

    def mark_submitted(self, tx_hash: str, chain: str) -> None:
        self.tx_hash = tx_hash
        self.chain = chain
        self.status = self.Status.SUBMITTED
        self.anchored_at = timezone.now()
        self.save(update_fields=["tx_hash", "chain", "status", "anchored_at"])
