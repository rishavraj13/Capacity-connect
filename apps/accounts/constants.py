"""Constants and choice enumerations for user accounts."""

from django.db import models


class UserRole(models.TextChoices):
    """Available user roles within the portal."""

    TRAINEE = "TRAINEE", "Trainee"
    TRAINER = "TRAINER", "Trainer"
    ADMIN = "ADMIN", "Admin"
