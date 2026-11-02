"""Expose an age-gated dry-run-first cleanup command with no model writes."""

from django.core.management.base import BaseCommand, CommandError

from apps.core.exceptions import CapacityConnectError
from apps.core.orphans import DEFAULT_MIN_AGE_HOURS, cleanup_orphans


class Command(BaseCommand):
    """Require an explicit --delete flag before removing unreferenced old files."""

    help = (
        "List aged unreferenced private/public files; dry-run unless --delete is set."
    )

    def add_arguments(self, parser: object) -> None:
        """Keep the minimum age and destructive intent visible in --help."""
        parser.add_argument("--min-age-hours", type=int, default=DEFAULT_MIN_AGE_HOURS)
        parser.add_argument("--delete", action="store_true")

    def handle(self, *args: object, **options: object) -> None:
        """Delegate reference/age safety to the service and print reviewable paths."""
        try:
            report = cleanup_orphans(options["min_age_hours"], options["delete"])
        except CapacityConnectError as exc:
            raise CommandError(exc.message) from exc
        for path in report.candidates:
            self.stdout.write(str(path))
        self.stdout.write(
            f"orphans={len(report.candidates)} deleted={len(report.deleted)} "
            f"dry_run={not options['delete']}"
        )
