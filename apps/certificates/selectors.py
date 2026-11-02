"""Scope private downloads and detach minimal public verification fields."""

import re

from django.db.models import QuerySet

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.certificates.constants import ID_PATTERN
from apps.certificates.dataclasses import Verification
from apps.certificates.models import Certificate


def visible_certificates(user: User) -> QuerySet[Certificate]:
    """Resolve download ownership before any private file is opened."""
    rows = Certificate.objects.select_related(
        "enrollment__trainee", "enrollment__course__trainer"
    )
    if not user.is_authenticated or not user.is_active or not user.is_approved:
        return rows.none()
    if user.role == UserRole.ADMIN:
        return rows
    if user.role == UserRole.TRAINER:
        return rows.filter(enrollment__course__trainer=user)
    return (
        rows.filter(enrollment__trainee=user)
        if user.role == UserRole.TRAINEE
        else rows.none()
    )


def certificates_for_trainee(user: User) -> QuerySet[Certificate]:
    """Keep the trainee's list distinct from staff download permissions."""
    return visible_certificates(user).filter(enrollment__trainee=user)


def public_verification(identifier: str) -> Verification | None:
    """Reject malformed and unknown IDs without exposing scores, grade or email."""
    if re.fullmatch(ID_PATTERN, identifier) is None:
        return None
    row = (
        Certificate.objects.select_related("enrollment__trainee", "enrollment__course")
        .filter(certificate_id=identifier)
        .first()
    )
    if row is None:
        return None
    trainee = row.enrollment.trainee
    return Verification(
        row.certificate_id,
        trainee.get_full_name() or trainee.username,
        row.enrollment.course.title,
        row.issued_on,
    )


def certificate_exists(enrollment: object) -> bool:
    """Report whether a successful completion created its durable record."""
    return Certificate.objects.filter(enrollment=enrollment).exists()
