"""Detach dashboard totals and rows from lazy ORM reads."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LineLoad:
    """Include active subjects with zero enrollment in the Admin handoff."""

    subject_id: int
    subject_name: str
    enrollments: int
    active_enrollments: int


@dataclass(frozen=True, slots=True)
class AssessmentStats:
    """Keep attempt counts separate from best-per-pair percentage statistics."""

    questionnaires_total: int
    submitted_attempts: int
    average_best_percent: Decimal
    pass_rate_percent: Decimal


@dataclass(frozen=True, slots=True)
class ParticipationStats:
    """Use the active/completed enrollment cohort for both participation counts."""

    enrolled_trainees: int
    attempted_trainees: int
    participation_rate_percent: Decimal


@dataclass(frozen=True, slots=True)
class AdminDashboard:
    """Carry bounded aggregate query results without database-backed template loops."""

    users_by_role: dict[str, int]
    pending_approvals: int
    courses_total: int
    courses_published: int
    enrollments_total: int
    enrollments_by_status: dict[str, int]
    line_load: tuple[LineLoad, ...]
    certificates_total: int
    certificates_by_grade: dict[str, int]
    assessments: AssessmentStats
    participation: ParticipationStats


@dataclass(frozen=True, slots=True)
class CourseStats:
    """Keep each trainer course's aggregates and safe detail links together."""

    course_id: int
    title: str
    is_published: bool
    enrolled: int
    active: int
    completed: int
    certificates: int
    avg_rating: Decimal | None
    rating_count: int
    questionnaires: int


@dataclass(frozen=True, slots=True)
class TrainerTotals:
    """Sum own-course counts while weighting the rating average over feedback rows."""

    courses_total: int
    courses_published: int
    enrolled: int
    active: int
    completed: int
    certificates: int
    avg_rating: Decimal | None
    rating_count: int
    questionnaires: int


@dataclass(frozen=True, slots=True)
class QuestionnaireLink:
    """Carry direct links to existing owner-scoped participation views."""

    questionnaire_id: int
    title: str
    course_title: str


@dataclass(frozen=True, slots=True)
class TrainerDashboard:
    """Expose only one eligible trainer's own course rows and totals."""

    courses: tuple[CourseStats, ...]
    totals: TrainerTotals
    questionnaires: tuple[QuestionnaireLink, ...]
