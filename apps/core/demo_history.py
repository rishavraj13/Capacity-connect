"""Populate professional history through the existing validated child services."""

from datetime import timedelta

from apps.core import clock
from apps.core.demo_files import demo_pdf, demo_png
from apps.profiles.models import ExternalCertificate, Qualification, WorkExperience
from apps.profiles.services import ensure_trainee_profile, save_child

EXPERIENCE_DAYS = 365
DEMO_HISTORY = (
    ("Diploma in Computer Applications", "Pune Skills Institute", "Data Assistant"),
    ("Bachelor of Commerce", "Delhi College", "Operations Associate"),
    ("Diploma in Business Studies", "Bengaluru Institute", "Project Assistant"),
)


def demo_history(graph: object) -> None:
    """Give approved trainees realistic education, employment and certificates."""
    for trainee, details in zip(graph.trainees, DEMO_HISTORY, strict=False):
        _professional_history(ensure_trainee_profile(trainee), details)
    for trainee, file in zip(graph.trainees, (demo_pdf(), demo_png()), strict=False):
        save_child(
            ExternalCertificate(profile=ensure_trainee_profile(trainee)),
            {
                "title": "Workplace Skills Foundation",
                "issuer": "Pragati Learning",
                "issued_on": clock.today(),
                "file": file,
            },
        )


def _professional_history(profile: object, details: tuple) -> None:
    """Keep professional child writes on the same validated service boundary."""
    degree, institution, role = details
    save_child(
        Qualification(profile=profile),
        {
            "degree": degree,
            "institution": institution,
            "year": clock.today().year - 1,
        },
    )
    save_child(
        WorkExperience(profile=profile),
        {
            "organisation": "Pragati Learning Cooperative",
            "role": role,
            "start_date": clock.today() - timedelta(days=EXPERIENCE_DAYS),
            "end_date": None,
            "description": "Supported practical workplace projects.",
        },
    )
