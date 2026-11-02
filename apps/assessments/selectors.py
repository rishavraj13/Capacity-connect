"""Provide scoped assessment metadata without exposing paper correctness."""

from django.db.models import (
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
)
from django.db.models.functions import Greatest

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.assessments.constants import DEPARTURE_LIMIT, AttemptStatus, DepartureStatus
from apps.assessments.dataclasses import Departure
from apps.assessments.models import Attempt, Question, Questionnaire
from apps.assessments.paper_selectors import paper_for as paper_for
from apps.assessments.participation_selectors import participation as participation
from apps.assessments.result_selectors import attempt_result as attempt_result
from apps.core import clock
from apps.courses.constants import EnrollmentStatus
from apps.courses.selectors import managed_courses


def managed_questionnaires(user: User) -> QuerySet[Questionnaire]:
    """Hide another trainer's authoring objects before any detail/edit lookup."""
    return Questionnaire.objects.filter(
        course__in=managed_courses(user)
    ).select_related("course", "trainer", "subject")


def managed_questions(user: User) -> QuerySet[Question]:
    """Resolve question ownership through the parent quiz's course."""
    return Question.objects.filter(
        questionnaire__in=managed_questionnaires(user)
    ).select_related("questionnaire__course")


def _usage_metadata(
    quizzes: QuerySet[Questionnaire], trainee: User
) -> QuerySet[Questionnaire]:
    """Annotate all-status usage and successful results without separate reads."""
    attempts = Attempt.objects.filter(questionnaire=OuterRef("pk"), trainee=trainee)
    quizzes = quizzes.annotate(
        attempts_used=Count(
            "attempts", filter=Q(attempts__trainee=trainee), distinct=True
        ),
        already_passed=Exists(
            attempts.filter(passed=True, status=AttemptStatus.SUBMITTED)
        ),
    )
    return quizzes.annotate(
        open_attempt_id=Subquery(
            attempts.filter(status=AttemptStatus.IN_PROGRESS).values("pk")[:1]
        ),
        enrollment_status=F("course__enrollments__status"),
        attempts_left=Greatest(
            F("max_attempts") - F("attempts_used"),
            Value(0),
            output_field=IntegerField(),
        ),
    )


def trainee_questionnaires(trainee: User) -> QuerySet[Questionnaire]:
    """Include ACTIVE/COMPLETED enrollment metadata with one joined SQL query."""
    quizzes = Questionnaire.objects.select_related("course", "subject")
    if (
        not trainee.is_active
        or not trainee.is_approved
        or trainee.role != UserRole.TRAINEE
    ):
        return _usage_metadata(quizzes.none(), trainee)
    quizzes = quizzes.filter(
        course__enrollments__trainee=trainee,
        course__enrollments__status__in=(
            EnrollmentStatus.ACTIVE,
            EnrollmentStatus.COMPLETED,
        ),
    )
    return _usage_metadata(quizzes, trainee)


def startable_questionnaires(trainee: User) -> QuerySet[Questionnaire]:
    """Keep dropped/non-enrolled quiz IDs out of the start endpoint."""
    return trainee_questionnaires(trainee).filter(
        enrollment_status=EnrollmentStatus.ACTIVE
    )


def next_deadlines_for(
    trainee: User, limit: int = DEPARTURE_LIMIT
) -> tuple[Departure, ...]:
    """Build upcoming departures in a single annotated joined query."""
    instant = clock.now()
    quizzes = (
        startable_questionnaires(trainee)
        .filter(deadline__gt=instant, attempts_left__gt=0, already_passed=False)
        .order_by("deadline", "pk")[: max(0, limit)]
    )
    return tuple(
        Departure(
            q.pk,
            q.title,
            q.course.title,
            q.subject.name,
            q.opens_at,
            q.deadline,
            DepartureStatus.OPEN if q.opens_at <= instant else DepartureStatus.UPCOMING,
            q.attempts_left,
        )
        for q in quizzes
    )


def owned_attempts(trainee: User) -> QuerySet[Attempt]:
    """Prevent guessed attempt IDs from reaching trainee read or submit flows."""
    attempts = Attempt.objects.select_related("questionnaire__course")
    if (
        not trainee.is_active
        or not trainee.is_approved
        or trainee.role != UserRole.TRAINEE
    ):
        return attempts.none()
    return attempts.filter(trainee=trainee)


def authoring_detail(user: User, pk: int) -> QuerySet[Questionnaire]:
    """Prefetch answer-bearing choices only for authorized authoring pages."""
    return (
        managed_questionnaires(user)
        .filter(pk=pk)
        .prefetch_related("questions__options")
    )


def history_for(trainee: User) -> QuerySet[Attempt]:
    """Keep a trainee's entire attempt history in one joined query."""
    return owned_attempts(trainee).order_by("-started_at", "-pk")


def passed_questionnaire_ids(enrollment: object) -> set[int]:
    """Provide B5 a read-only completion handoff without issuing completion here."""
    return set(
        Attempt.objects.filter(
            trainee_id=enrollment.trainee_id,
            questionnaire__course_id=enrollment.course_id,
            passed=True,
            status=AttemptStatus.SUBMITTED,
        ).values_list("questionnaire_id", flat=True)
    )


def has_passed(trainee: User, questionnaire: Questionnaire) -> bool:
    """Reuse persisted successful outcomes for later completion logic."""
    return Attempt.objects.filter(
        trainee=trainee,
        questionnaire=questionnaire,
        passed=True,
        status=AttemptStatus.SUBMITTED,
    ).exists()


def conflicting_course_questionnaires(
    course: object, trainer: User, subject: object
) -> QuerySet[Questionnaire]:
    """Keep derived assessment references consistent when course metadata changes."""
    return Questionnaire.objects.filter(course=course).exclude(
        trainer=trainer, subject=subject
    )


def question_initial(question: Question) -> dict:
    """Build a draft edit form from one ordered, owner-authorized option read."""
    options = list(question.options.all())
    return {
        "text": question.text,
        "marks": question.marks,
        "options": "\n".join(option.text for option in options),
        "correct_option": next(
            (index for index, option in enumerate(options, 1) if option.is_correct), 1
        ),
    }


def questionnaires_for_course(user: User, course: object) -> QuerySet[Questionnaire]:
    """Keep course-specific authoring list reads inside selectors."""
    return managed_questionnaires(user).filter(course=course)


def result_history(user: User, questionnaire: Questionnaire) -> QuerySet[Attempt]:
    """Provide staff links to finalized results without per-row trainee lookups."""
    from apps.assessments.result_selectors import visible_results

    return (
        visible_results(user)
        .filter(questionnaire=questionnaire)
        .select_related("trainee")
    )
