"""Verify shared HTTP coordination reports service validation failures."""

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_service_validation_error_is_rendered(
    client: Client, monkeypatch: object
) -> None:
    """Preserve user feedback when state changes between form and service checks."""

    def reject(data: dict) -> None:
        """Simulate a catalog lifecycle race after form validation."""
        raise ValidationError("Catalog changed; retry.")

    monkeypatch.setattr("apps.catalog.services.create_subject", reject)
    client.force_login(UserFactory(active_admin=True))
    response = client.post(reverse("catalog:subject_create"), {"name": "Science"})
    assert response.status_code == 200
    assert "Catalog changed; retry." in response.context["form"].non_field_errors()
