"""Represent role profiles without duplicating account or authorization state."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.storage import PrivateStorage
from apps.core.uploads import UploadPath
from apps.core.validators import validate_certificate, validate_photo
from apps.profiles.constants import (
    MAX_YEARS_EXPERIENCE,
    MIN_YEARS_EXPERIENCE,
    QUALIFICATION_YEAR_MAX,
    QUALIFICATION_YEAR_MIN,
    TEXT_MAX_LENGTH,
)


class TraineeProfile(TimeStampedModel):
    """Keep trainee history available across later account role changes."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainee_profile",
    )
    bio = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    skills = models.ManyToManyField(
        "catalog.Skill", blank=True, related_name="trainee_profiles"
    )
    photo = models.FileField(
        storage=PrivateStorage(),
        upload_to=UploadPath("trainee_photos", settings.PHOTO_EXTENSIONS),
        blank=True,
        validators=[validate_photo],
    )


class Qualification(TimeStampedModel):
    """Associate educational history exclusively with its owning profile."""

    profile = models.ForeignKey(
        TraineeProfile, on_delete=models.CASCADE, related_name="qualifications"
    )
    degree = models.CharField(max_length=TEXT_MAX_LENGTH)
    institution = models.CharField(max_length=TEXT_MAX_LENGTH)
    year = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(QUALIFICATION_YEAR_MIN),
            MaxValueValidator(QUALIFICATION_YEAR_MAX),
        ]
    )


class WorkExperience(TimeStampedModel):
    """Keep employment dates valid even for direct database writes."""

    profile = models.ForeignKey(
        TraineeProfile, on_delete=models.CASCADE, related_name="work_experiences"
    )
    organisation = models.CharField(max_length=TEXT_MAX_LENGTH)
    role = models.CharField(max_length=TEXT_MAX_LENGTH)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        """Permit ongoing employment while rejecting reversed date ranges."""

        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="experience_dates_ordered",
            )
        ]


class ExternalCertificate(TimeStampedModel):
    """Store supporting evidence behind the same privacy rules as the profile."""

    profile = models.ForeignKey(
        TraineeProfile, on_delete=models.CASCADE, related_name="external_certificates"
    )
    title = models.CharField(max_length=TEXT_MAX_LENGTH)
    issuer = models.CharField(max_length=TEXT_MAX_LENGTH)
    file = models.FileField(
        storage=PrivateStorage(),
        upload_to=UploadPath("external_certificates", settings.CERTIFICATE_EXTENSIONS),
        validators=[validate_certificate],
    )
    issued_on = models.DateField()


class TrainerProfile(TimeStampedModel):
    """Publish trainer details without exposing trainee history."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_profile",
    )
    bio = models.TextField(blank=True)
    headline = models.CharField(max_length=TEXT_MAX_LENGTH, blank=True)
    years_experience = models.PositiveSmallIntegerField(
        default=MIN_YEARS_EXPERIENCE,
        validators=[
            MinValueValidator(MIN_YEARS_EXPERIENCE),
            MaxValueValidator(MAX_YEARS_EXPERIENCE),
        ],
    )
    photo = models.FileField(
        storage=PrivateStorage(),
        upload_to=UploadPath("trainer_photos", settings.PHOTO_EXTENSIONS),
        blank=True,
        validators=[validate_photo],
    )
