"""Core domain exception hierarchy."""


class CapacityConnectError(Exception):
    """Base domain exception for all Capacity Connect errors."""

    def __init__(self, message: str = "A domain error occurred.") -> None:
        """Initialize domain exception with a descriptive message."""
        super().__init__(message)
        self.message = message


class UserManagementError(CapacityConnectError):
    """Base domain exception for user management and administration errors."""


class SelfModificationError(UserManagementError):
    """Raised when an admin attempts self-rejection or self-demotion."""


class LastAdminProtectionError(UserManagementError):
    """Raised when an action would remove the last active administrator."""


class InvalidRoleError(UserManagementError):
    """Raised when an invalid or unauthorized role transition occurs."""
