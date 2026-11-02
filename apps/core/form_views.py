"""Share HTTP form coordination without moving writes into views."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.exceptions import CapacityConnectError


@dataclass
class FormAction:
    """Group form presentation details to keep view interfaces small."""

    form_class: type[forms.BaseForm]
    save: Callable
    instance: Any = None
    success_url: str = "catalog:subject_list"
    title: str = "Edit details"


@require_http_methods(["GET", "POST"])
def form_response(request: HttpRequest, action: FormAction) -> HttpResponse:
    """Keep validation failures visible while services own persistence."""
    form = action.form_class(
        request.POST if request.method == "POST" else None,
        request.FILES or None,
        instance=action.instance,
    )
    if request.method == "POST" and form.is_valid():
        try:
            action.save(form.cleaned_data)
            return redirect(action.success_url)
        except CapacityConnectError as exc:
            form.add_error(None, exc.message)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, "shared/form.html", {"form": form, "title": action.title})


def action_response(
    request: HttpRequest, action: Callable, destination: str
) -> HttpResponse:
    """Translate domain rejection into user feedback for explicit POST actions."""
    try:
        action()
    except CapacityConnectError as exc:
        messages.error(request, exc.message)
    return redirect(destination)
