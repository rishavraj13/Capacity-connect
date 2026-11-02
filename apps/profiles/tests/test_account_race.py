"""Exercise the database uniqueness race after form and model validation."""

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _race_hook(owner_id: int) -> Any:
    """Arrange a real constraint collision after service validation has passed."""
    real_clean = User.full_clean

    def insert_competitor(user: User, *args: Any, **kwargs: Any) -> None:
        """Insert the competing case variant before the account database write."""
        real_clean(user, *args, **kwargs)
        if user.pk == owner_id and user.email == "race@example.com" and not kwargs:
            UserFactory(email="RACE@EXAMPLE.COM")

    return insert_competitor


def test_account_email_database_race_becomes_form_error(
    client: Client, monkeypatch: Any
) -> None:
    """Turn a real Lower(email) database collision into recoverable form feedback."""
    owner = UserFactory(approved_trainee=True)
    original = owner.email
    monkeypatch.setattr(User, "full_clean", _race_hook(owner.pk))
    client.force_login(owner)
    response = client.post(
        reverse("profiles:account_edit"), {"email": "race@example.com"}
    )
    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    owner.refresh_from_db()
    assert owner.email == original
    assert User.objects.count() == 1  # The simulated competing insert rolls back too.


def test_unrelated_integrity_error_is_not_hidden(monkeypatch: Any) -> None:
    """Keep non-email persistence failures visible instead of misreporting them."""
    from django.db import IntegrityError

    from apps.profiles.services import update_account

    user = UserFactory()

    def fail_save(instance: User, *args: Any, **kwargs: Any) -> None:
        """Represent a database failure unrelated to the email constraint."""
        raise IntegrityError("Unrelated database failure")

    monkeypatch.setattr(User, "save", fail_save)
    with pytest.raises(IntegrityError, match="Unrelated database failure"):
        update_account(user, {"email": user.email, "first_name": "A", "last_name": "B"})
