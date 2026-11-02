"""Translate validated persistence failures at the domain write boundary."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction

from apps.core.exceptions import CapacityConnectError


def validated_save(instance: models.Model, error: type[CapacityConnectError]) -> None:
    """Report validation and constraint races without leaving broken transactions."""
    try:
        instance.full_clean()
        with transaction.atomic():
            instance.save()
    except ValidationError as exc:
        raise error(" ".join(exc.messages)) from exc
    except IntegrityError as exc:
        raise error("Conflicting data; refresh the form and retry.") from exc
