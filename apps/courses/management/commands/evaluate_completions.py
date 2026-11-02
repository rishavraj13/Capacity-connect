"""Retry failed certificate completions without duplicating successful work."""

from django.core.management.base import BaseCommand

from apps.certificates.selectors import certificate_exists
from apps.courses.completion import evaluate_completion
from apps.courses.completion_selectors import active_enrollments, completion_status
from apps.courses.constants import EnrollmentStatus


class Command(BaseCommand):
    """Provide an explicit, repeatable recovery path instead of implicit signals."""

    help = "Re-evaluate ACTIVE enrollments and retry failed certificate generation."

    def handle(self, *args: object, **options: object) -> None:
        """Report checked, transitioned, issued and failed candidates."""
        counts = {"checked": 0, "completed": 0, "certificates": 0, "failed": 0}
        for enrollment in active_enrollments().iterator():
            counts["checked"] += 1
            eligible = completion_status(enrollment).requirements_met
            if evaluate_completion(enrollment):
                counts["completed"] += 1
                counts["certificates"] += int(certificate_exists(enrollment))
            elif eligible:
                enrollment.refresh_from_db()
                counts["failed"] += int(enrollment.status == EnrollmentStatus.ACTIVE)
        self.stdout.write(" ".join(f"{key}={value}" for key, value in counts.items()))
