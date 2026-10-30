"""Unit tests for core exception classes and abstract models."""

from apps.core.exceptions import CapacityConnectError
from apps.core.models import TimeStampedModel


def test_capacity_connect_error_default_message() -> None:
    """Verify default error message on domain exception."""
    error = CapacityConnectError()
    assert error.message == "A domain error occurred."
    assert str(error) == "A domain error occurred."


def test_capacity_connect_error_custom_message() -> None:
    """Verify custom error message on domain exception."""
    custom_msg: str = "Specific domain issue."
    error = CapacityConnectError(custom_msg)
    assert error.message == custom_msg
    assert str(error) == custom_msg


def test_timestamped_model_is_abstract() -> None:
    """Verify TimeStampedModel is marked as an abstract model."""
    assert TimeStampedModel._meta.abstract is True
