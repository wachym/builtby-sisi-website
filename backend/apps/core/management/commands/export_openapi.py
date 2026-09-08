"""Export the OpenAPI schema.

This file is the contract between the two runtimes. CI runs this command, then
regenerates the TypeScript client in app/bbs; if the two disagree, the build
fails there instead of a user finding it at runtime.

    python manage.py export_openapi --output openapi.json
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from bbsbackend.api import api


class Command(BaseCommand):
    help = "Write the OpenAPI schema for the versioned API to a file or stdout."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            default="-",
            help="Destination path, or '-' for stdout (default).",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Exit non-zero if the file on disk differs from the current schema.",
        )
        parser.add_argument("--indent", type=int, default=2)

    def handle(self, *args, **options):
        schema = json.dumps(
            api.get_openapi_schema(), indent=options["indent"], sort_keys=True
        )

        if options["output"] == "-":
            self.stdout.write(schema)
            return

        destination = Path(options["output"])

        if options["check"]:
            if not destination.is_file():
                raise CommandError(f"{destination} does not exist; run without --check.")
            if destination.read_text(encoding="utf-8").strip() != schema.strip():
                raise CommandError(
                    f"{destination} is stale. Run: python manage.py export_openapi "
                    f"-o {destination}"
                )
            self.stdout.write(self.style.SUCCESS(f"{destination} is up to date."))
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(schema + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {destination}"))
