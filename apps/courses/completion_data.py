"""Detach completion handoffs from database-backed template loops."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class QuestionnaireCompletion:
    """Explain the remaining quiz work with safe metadata only."""

    title: str
    passed: bool
    attempts_left: int
    deadline: datetime


@dataclass(frozen=True, slots=True)
class CompletionStatus:
    """Retain recorded completion while exposing current remaining requirements."""

    modules_done: int
    modules_total: int
    questionnaires: tuple[QuestionnaireCompletion, ...]
    is_complete: bool

    @property
    def requirements_met(self) -> bool:
        """Share one requirements decision between triggers and retry reporting."""
        return (
            self.modules_total > 0
            and self.modules_done == self.modules_total
            and all(q.passed for q in self.questionnaires)
        )
