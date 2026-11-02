"""Render existing private uploads without asking storage for public URLs."""

from typing import Any

from django.forms import ClearableFileInput


class PrivateFileInput(ClearableFileInput):
    """Keep upload replacement and clearing independent of public media links."""

    template_name = "core/private_file_input.html"

    def is_initial(self, value: Any) -> bool:
        """Detect an existing upload by its stored name rather than its URL."""
        return bool(value and getattr(value, "name", False))
