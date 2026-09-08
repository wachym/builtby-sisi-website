"""Append one complete Loop to the ledger, for demonstration and local work.

The sequence mirrors the programme's central claim: a perception event becomes
agent work, becomes human and client acceptance, becomes settlement, becomes
yield. Real engagements append the same event types through the same service.

Refuses to run with DEBUG off, so demonstration facts cannot be mixed into a
production chain.

    python manage.py ledger_demo
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.ledger import services
from apps.ledger.models import ActorKey, ActorType
from apps.ledger.signers import Ed25519Signer


class Command(BaseCommand):
    help = "Append a demonstration Loop (perception -> work -> acceptance -> settlement)."

    def add_arguments(self, parser):
        parser.add_argument("--subject", default="engagement:demo-1")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "ledger_demo only runs with DEBUG on. A production ledger records "
                "facts, not demonstrations."
            )

        subject = options["subject"]
        started = timezone.now() - timedelta(hours=6)

        actors = {}
        for handle, actor_type in [
            ("rig-01", ActorType.DEVICE),
            ("foreman", ActorType.AGENT),
            ("cartographer", ActorType.AGENT),
            ("sisi-operator", ActorType.HUMAN),
            ("client-demo", ActorType.HUMAN),
        ]:
            signer = Ed25519Signer.generate()
            actor, _ = ActorKey.objects.update_or_create(
                handle=handle,
                defaults={
                    "actor_type": actor_type,
                    "public_key": signer.public_key_hex,
                    "is_active": True,
                },
            )
            actors[handle] = (actor, signer)

        steps = [
            ("rig-01", "perception.captured", {
                "device": "rig-01", "detection": "shelf_count_mismatch",
                "expected": 24, "observed": 21, "confidence": 0.94,
                "model": "yolo-inventory@2.1.0",
            }),
            ("foreman", "agent.run.started", {
                "agent": "foreman", "trigger": "perception.captured", "budget_usd": 2.0,
            }),
            ("foreman", "agent.tool.called", {
                "tool": "github.search_code", "args": {"query": "inventory reconcile"},
                "cost_usd": 0.08,
            }),
            ("cartographer", "estimate.proposed", {
                "milestones": 1, "hours": 6, "amount": "1800.00", "currency": "USDC",
            }),
            ("sisi-operator", "human.approved", {
                "what": "estimate", "approver": "sisi-operator",
            }),
            ("foreman", "commit.pushed", {
                "repo": "client/inventory-svc", "sha": "9f2c1ab", "tests": "passing",
            }),
            ("foreman", "milestone.delivered", {
                "milestone": 1, "evidence": ["commit:9f2c1ab", "ci:passed"],
            }),
            ("client-demo", "client.accepted", {
                "milestone": 1, "signed_with": "passkey",
            }),
            ("sisi-operator", "escrow.released", {
                "milestone": 1, "amount": "1800.00", "currency": "USDC",
                "chain": settings.LEDGER_ANCHOR_CHAIN, "tx": "0xdemo",
            }),
            ("sisi-operator", "yield.accrued", {
                "amount": "4.31", "currency": "USDC", "beneficiary": "client",
                "days_held": 9,
            }),
        ]

        for index, (handle, event_type, payload) in enumerate(steps):
            actor, signer = actors[handle]
            event = services.append_event(
                event_type=event_type,
                subject=subject,
                actor=actor,
                payload=payload,
                occurred_at=started + timedelta(minutes=index * 17),
                signer=signer,
            )
            self.stdout.write(f"  #{event.seq:>3} {event.type:<24} {event.hash[:16]}...")

        report = services.verify_chain()
        if not report.ok:
            raise CommandError("demo produced an invalid chain; this is a bug")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"appended {len(steps)} events for {subject}; chain verifies "
                f"at head #{report.head_seq}"
            )
        )
