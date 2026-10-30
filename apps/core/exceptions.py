"""Core domain exception hierarchy."""


class CapacityConnectError(Exception):
    """Base domain exception for all Capacity Connect errors."""

    def __init__(self, message: str = "A domain error occurred.") -> None:
        """Initialize domain exception with a descriptive message."""
        super().__init__(message)
        self.message = message
