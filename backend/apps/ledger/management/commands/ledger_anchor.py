"""Build the Merkle anchor for a day.

Runs as a scheduled task once Celery lands in Phase 2; until then it is a cron
line or a manual command. Publishing the root on-chain happens in Phase 5 —
this command records it as pending.

    python manage.py ledger_anchor            # yesterday, UTC
    python manage.py ledger_anchor --date 2026-09-07
"""

from __future__ import annotations

from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.ledger.services import build_anchor


class Command(BaseCommand):
    help = "Compute and record the Merkle root for one UTC day of the ledger."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="period",
            default=None,
            help="UTC date as YYYY-MM-DD. Defaults to yesterday.",
        )
        parser.add_argument("--chain", default=None)

    def handle(self, *args, **options):
        if options["period"]:
            try:
                period = date.fromisoformat(options["period"])
            except ValueError as exc:
                raise CommandError("--date must be YYYY-MM-DD") from exc
        else:
            period = (timezone.now() - timedelta(days=1)).date()

        anchor = build_anchor(period, chain=options["chain"])
        self.stdout.write(
            self.style.SUCCESS(
                f"{anchor.period}: {anchor.event_count} event(s), "
                f"root {anchor.merkle_root}, status {anchor.status}"
            )
        )
