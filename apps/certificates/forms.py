"""Normalize public lookup input before applying the same identifier rule."""

from django import forms

from apps.certificates.constants import ID_PATTERN


class VerificationForm(forms.Form):
    """Keep certificate lookup a safe GET operation."""

    certificate_id = forms.RegexField(regex=rf"\A{ID_PATTERN}\Z", max_length=13)
