"""Expose service-driven demo creation with an explicit safety override."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.core.demo_services import seed_demo_data
from apps.core.exceptions import CapacityConnectError


class Command(BaseCommand):
    """Print public demo logins once and never seed production implicitly."""

    help = (
        "Create an idempotent demo through services; "
        "refuses DEBUG=False/prod unless --force."
    )

    def add_arguments(self, parser: object) -> None:
        """Make the production override visible in --help."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Explicitly allow demo data in DEBUG=False/prod.",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Delegate writes and print development-only demo credentials."""
        try:
            report = seed_demo_data(options["force"])
        except (CapacityConnectError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write("MODEL | ROWS")
        for label, count in sorted(report["counts"].items()):
            self.stdout.write(f"{label} | {count}")
        self.stdout.write("USERNAME | ROLE | STATUS")
        for row in report["logins"]:
            self.stdout.write(" | ".join(row))
        self.stdout.write(f"Demo password (development only): {settings.DEMO_PASSWORD}")
