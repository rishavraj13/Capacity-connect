"""Provide role-correct profiles and valid in-memory upload fixtures."""

from datetime import date
from io import BytesIO

import factory
from django.core.files.uploadedfile import SimpleUploadedFile
from factory.django import DjangoModelFactory
from PIL import Image

from apps.accounts.tests.factories import UserFactory
from apps.profiles.models import (
    ExternalCertificate,
    Qualification,
    TraineeProfile,
    TrainerProfile,
    WorkExperience,
)


def photo_upload(name: str = "photo.png") -> SimpleUploadedFile:
    """Generate actual image bytes rather than trusting filename-only fixtures."""
    stream = BytesIO()
    Image.new("RGB", (2, 2)).save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


def pdf_upload(name: str = "proof.pdf") -> SimpleUploadedFile:
    """Exercise the specified PDF signature contract."""
    return SimpleUploadedFile(name, b"%PDF-1.7\n%%EOF", content_type="application/pdf")


class TraineeProfileFactory(DjangoModelFactory):
    """Create owner-isolated trainee histories."""

    class Meta:
        """Bind fixtures to trainee profiles."""

        model = TraineeProfile

    user = factory.SubFactory(UserFactory, approved_trainee=True)


class TrainerProfileFactory(DjangoModelFactory):
    """Keep trainer fixtures distinct from trainee permissions."""

    class Meta:
        """Bind fixtures to trainer profiles."""

        model = TrainerProfile

    user = factory.SubFactory(UserFactory, approved_trainer=True)


class QualificationFactory(DjangoModelFactory):
    """Supply deterministic education history."""

    class Meta:
        """Bind fixtures to education records."""

        model = Qualification

    profile = factory.SubFactory(TraineeProfileFactory)
    degree = "BSc"
    institution = "Test University"
    year = 2020


class WorkExperienceFactory(DjangoModelFactory):
    """Supply valid ongoing employment dates."""

    class Meta:
        """Bind fixtures to employment records."""

        model = WorkExperience

    profile = factory.SubFactory(TraineeProfileFactory)
    organisation = "Test Organisation"
    role = "Analyst"
    start_date = date(2020, 1, 1)


class ExternalCertificateFactory(DjangoModelFactory):
    """Supply private evidence with actual allowed bytes."""

    class Meta:
        """Bind fixtures to supporting certificates."""

        model = ExternalCertificate

    profile = factory.SubFactory(TraineeProfileFactory)
    title = "External Award"
    issuer = "Test Institution"
    issued_on = date(2020, 1, 1)
    file = factory.LazyFunction(pdf_upload)
