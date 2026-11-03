"""Adapt numbered authoring inputs to the existing line-oriented field."""

from django import forms

from apps.assessments.constants import MAX_OPTIONS


class OptionRows(forms.MultiWidget):
    """Preserve the existing options payload for callers while rendering six rows."""

    template_name = "assessments/option_rows.html"

    def __init__(self) -> None:
        """Keep individual rows optional so the grouped validator counts them."""
        super().__init__([forms.TextInput() for _ in range(MAX_OPTIONS)])

    def use_required_attribute(self, initial: object) -> bool:
        """Leave the minimum row count to the grouped server validator."""
        return False

    def decompress(self, value: str | None) -> list[str]:
        """Restore bound or initial option text in the original row order."""
        return value.splitlines() if value else []

    def value_from_datadict(self, data: dict, files: dict, name: str) -> str:
        """Accept either the original field or the six visible row inputs."""
        if name in data:
            return data[name]
        return "\n".join(
            value or "" for value in super().value_from_datadict(data, files, name)
        )
