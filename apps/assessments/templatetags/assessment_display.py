"""Render authoring status using the shared start-window rule."""

from datetime import datetime

from django import template

from apps.assessments.models import Questionnaire
from apps.assessments.rules import start_window_state

register = template.Library()


@register.filter
def questionnaire_status(quiz: Questionnaire, instant: datetime) -> str:
    """Keep timing and readiness words separate from color or form controls."""
    return (
        (start_window_state(quiz, instant) or "Open")
        if quiz.ready
        else "Draft / not ready"
    )
