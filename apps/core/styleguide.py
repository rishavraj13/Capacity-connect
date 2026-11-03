"""Expose the component catalogue only for development review."""

from django import forms
from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe


class SampleForm(forms.Form):
    """Show a labelled field with help and validation feedback."""

    station = forms.CharField(help_text="Use the name shown on the station sign.")
    platform = forms.CharField(required=False, help_text="Optional platform label.")


@require_safe
def styleguide(request: HttpRequest) -> HttpResponse:
    """Render component samples without using application data."""
    if not settings.DEBUG:
        raise Http404
    departures = (
        ("Notice", "Orientation at Central", "09:15"),
        ("Deadline", "Submit the network quiz", "14:30"),
        ("New content", "Signal safety workbook", "16:00"),
    )
    return render(
        request,
        "styleguide.html",
        {"sample_form": SampleForm({}), "departures": departures},
    )
