"""Verify the explicit retry command recovers PDF failures and stays idempotent."""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.assessments.tests.factories import MOMENT
from apps.certificates.models import Certificate
from apps.core import clock
from apps.courses.services import complete_module
from apps.courses.tests.completion_factories import completion_flow, pass_quiz


@pytest.mark.django_db
def test_evaluate_completions_counts_retry_and_idempotence(monkeypatch: object) -> None:
    """Keep failed candidates ACTIVE until an explicit successful re-evaluation."""
    monkeypatch.setattr(clock, "now", lambda: MOMENT)
    monkeypatch.setattr(clock, "today", lambda: MOMENT.date())
    enrollment, module, quiz, question = completion_flow()
    complete_module(enrollment.trainee, enrollment, module)
    with patch(
        "apps.certificates.services.render_certificate_pdf",
        side_effect=ValueError("bad PDF"),
    ):
        pass_quiz(enrollment, quiz, question)
        failed = StringIO()
        call_command("evaluate_completions", stdout=failed)
    assert failed.getvalue().strip() == "checked=1 completed=0 certificates=0 failed=1"
    output = StringIO()
    call_command("evaluate_completions", stdout=output)
    assert output.getvalue().strip() == "checked=1 completed=1 certificates=1 failed=0"
    again = StringIO()
    call_command("evaluate_completions", stdout=again)
    assert again.getvalue().strip() == "checked=0 completed=0 certificates=0 failed=0"
    assert Certificate.objects.count() == 1
