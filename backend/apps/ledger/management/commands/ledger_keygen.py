"""Generate an Ed25519 keypair and optionally register the actor.

Local development only. In production the private half never exists outside
the signer service, and this command is not how keys are made.

    python manage.py ledger_keygen --handle sisi-dev --type system --register
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.ledger.models import ActorKey, ActorType
from apps.ledger.signers import Ed25519Signer


class Command(BaseCommand):
    help = "Generate an Ed25519 keypair for a ledger actor (development use)."

    def add_arguments(self, parser):
        parser.add_argument("--handle", default="local-dev")
        parser.add_argument(
            "--type", dest="actor_type", default=ActorType.SYSTEM, choices=ActorType.values
        )
        parser.add_argument(
            "--register",
            action="store_true",
            help="Create or update the ActorKey row with the public half.",
        )

    def handle(self, *args, **options):
        signer = Ed25519Signer.generate()

        if options["register"]:
            actor, created = ActorKey.objects.update_or_create(
                handle=options["handle"],
                defaults={
                    "actor_type": options["actor_type"],
                    "public_key": signer.public_key_hex,
                    "is_active": True,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{'created' if created else 'updated'} actor {actor.handle}"
                )
            )

        self.stdout.write("")
        self.stdout.write(f"handle:      {options['handle']}")
        self.stdout.write(f"public key:  {signer.public_key_hex}")
        self.stdout.write(f"private key: {signer.private_key_hex}")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Put the private key in .env as LEDGER_SIGNING_KEY. Never commit it, "
                "and never use a locally generated key in production."
            )
        )
