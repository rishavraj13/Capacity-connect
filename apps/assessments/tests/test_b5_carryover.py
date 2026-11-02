"""Cover externally callable empty scopes and integer grading contracts."""

import ast
from pathlib import Path

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.assessments.selectors import owned_attempts


@pytest.mark.django_db
@pytest.mark.parametrize(
    "traits", [{"is_active": False}, {"is_approved": False}, {"approved_trainer": True}]
)
def test_ineligible_owned_attempts_scope_is_empty(traits: dict) -> None:
    """Prove the selector guard reachable independently of HTTP decorators."""
    assert not owned_attempts(UserFactory(**traits)).exists()


def test_grading_uses_no_float_operations() -> None:
    """Pin integer/Decimal grading by rejecting float literals and conversions."""
    source = Path("apps/assessments/grading.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(
        isinstance(n, ast.Constant) and isinstance(n.value, float)
        for n in ast.walk(tree)
    )
    assert not any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "float"
        for n in ast.walk(tree)
    )
