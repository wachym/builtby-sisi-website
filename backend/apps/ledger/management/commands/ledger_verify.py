"""Verify the chain from the command line.

Intended for CI and for a human who wants an answer without trusting the API:
    python manage.py ledger_verify --signatures
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.ledger import services


class Command(BaseCommand):
    help = "Re-derive the ledger hash chain and report any break."

    def add_arguments(self, parser):
        parser.add_argument("--since-seq", type=int, default=0)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument(
            "--signatures",
            action="store_true",
            help="Also verify every stored signature against its actor key.",
        )

    def handle(self, *args, **options):
        report = services.verify_chain(
            since_seq=options["since_seq"], limit=options["limit"]
        )

        self.stdout.write(
            f"checked {report.checked} event(s); head #{report.head_seq} "
            f"{report.head_hash[:16]}..."
        )

        problems = list(report.problems)
        if options["signatures"]:
            signature_problems = services.verify_signatures(since_seq=options["since_seq"])
            problems.extend(signature_problems)
            self.stdout.write(f"signature problems: {len(signature_problems)}")

        if problems:
            for problem in problems:
                self.stderr.write(f"  #{problem.seq}: {problem.reason}")
            raise CommandError(f"chain verification failed: {len(problems)} problem(s)")

        self.stdout.write(self.style.SUCCESS("chain verified"))
