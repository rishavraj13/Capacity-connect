"""Detach learner-visible assessment data from correctness-bearing ORM models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from apps.assessments.constants import MIN_MARKS, DepartureStatus


@dataclass(frozen=True, slots=True)
class Departure:
    """Carry deadline information without any paper or answer data."""

    questionnaire_id: int
    title: str
    course_title: str
    subject_name: str
    opens_at: datetime
    deadline: datetime
    status: DepartureStatus
    attempts_left: int


@dataclass(frozen=True, slots=True)
class ParticipationRow:
    """Include zero-attempt enrollment rows without lazy database reads."""

    trainee_id: int
    trainee_name: str
    attempts_used: int
    best_percent: Decimal
    passed: bool
    last_attempt_at: datetime | None


@dataclass(frozen=True, slots=True)
class QuestionnaireStats:
    """Keep aggregate participation presentation independent of query evaluation."""

    enrolled: int
    attempted: int
    passed: int
    average_best_percent: Decimal
    pass_rate: Decimal


@dataclass(frozen=True, slots=True)
class PaperOption:
    """Make correctness information structurally unavailable to take-page rendering."""

    option_id: int
    text: str


@dataclass(frozen=True, slots=True)
class PaperQuestion:
    """Expose only question presentation fields and safe option data."""

    question_id: int
    text: str
    order: int
    marks: int
    options: tuple[PaperOption, ...]


@dataclass(frozen=True, slots=True)
class ResultQuestion:
    """Reveal correct-option text only under the result disclosure policy."""

    question_id: int
    text: str
    marks: int
    selected_text: str | None
    is_correct: bool
    correct_option: str | None


@dataclass(frozen=True, slots=True)
class AttemptResult:
    """Keep hidden option flags out of result contexts when attempts remain."""

    attempt_id: int
    title: str
    score: int
    percent: Decimal
    passed: bool
    status: str
    questions: tuple[ResultQuestion, ...]


@dataclass(frozen=True, slots=True)
class QuestionInput:
    """Group authoring input to keep service signatures below four parameters."""

    text: str
    options: tuple[str, ...]
    correct_index: int
    marks: int = MIN_MARKS
