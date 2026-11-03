"""Describe private upload settings without exposing paths or changing validation."""

from django import template
from django.conf import settings
from django.forms.boundfield import BoundField
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html

from apps.library.constants import ResourceKind

register = template.Library()


@register.inclusion_tag("components/profile_upload.html")
def profile_upload(field: BoundField) -> dict:
    """Associate the live limit with the matching private file control."""
    photo = field.name == "photo"
    extensions = settings.PHOTO_EXTENSIONS if photo else settings.CERTIFICATE_EXTENSIONS
    size = settings.PHOTO_MAX_BYTES if photo else settings.CERTIFICATE_MAX_BYTES
    help_id = f"{field.auto_id}_upload_help"
    described_by = " ".join(filter(None, (field.aria_describedby, help_id)))
    return {
        "field": field,
        "widget": field.as_widget(attrs={"aria-describedby": described_by}),
        "help_id": help_id,
        "upload_help": format_html(
            "Allowed types: {}. Maximum size: {}.",
            ", ".join(extensions).upper(),
            filesizeformat(size),
        ),
    }


@register.inclusion_tag("components/library_upload.html")
def library_upload(field: BoundField) -> dict:
    """Link the upload control to the existing per-kind validation settings."""
    help_id = f"{field.auto_id}_upload_help"
    described_by = " ".join(filter(None, (field.aria_describedby, help_id)))
    return {
        "field": field,
        "widget": field.as_widget(attrs={"aria-describedby": described_by}),
        "help_id": help_id,
        "limits": [
            (
                kind.label,
                ", ".join(settings.LIBRARY_UPLOAD_EXTENSIONS[kind]),
                filesizeformat(settings.LIBRARY_UPLOAD_LIMITS[kind]),
            )
            for kind in ResourceKind
        ],
    }


@register.inclusion_tag("components/date_field.html")
def format_date_field(field: BoundField) -> dict:
    """Keep date hints linked without affecting the field's accepted formats."""
    hint_id = f"{field.auto_id}_format"
    described_by = " ".join(filter(None, (field.aria_describedby, hint_id)))
    return {
        "field": field,
        "widget": field.as_widget(attrs={"aria-describedby": described_by}),
        "hint_id": hint_id,
    }
