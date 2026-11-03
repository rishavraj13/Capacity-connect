"""Describe private upload settings without exposing paths or changing validation."""

from django import template
from django.conf import settings
from django.forms.boundfield import BoundField
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html

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
