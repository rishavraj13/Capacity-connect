"""Protect assessment history and concurrency invariants at the database boundary."""

from django.conf import settings
from django.db import models

from apps.assessments.constants import (
    DEFAULT_PASS_PERCENT,
    FIRST_QUESTION_ORDER,
    MAX_ATTEMPTS,
    MAX_DURATION_MINUTES,
    MAX_PASS_PERCENT,
    MIN_ATTEMPTS,
    MIN_DURATION_MINUTES,
    MIN_MARKS,
    MIN_PASS_PERCENT,
    TITLE_MAX_LENGTH,
    ZERO_PERCENT,
    AttemptStatus,
)
from apps.core.models import TimeStampedModel


class Questionnaire(TimeStampedModel):
    """Keep quiz timing and trainer/subject snapshots tied to a protected course."""

    course = models.ForeignKey(
        "courses.Course", on_delete=models.PROTECT, related_name="questionnaires"
    )
    subject = models.ForeignKey(
        "catalog.Subject", on_delete=models.PROTECT, related_name="questionnaires"
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="questionnaires",
    )
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    opens_at = models.DateTimeField()
    deadline = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    pass_percent = models.PositiveIntegerField(default=DEFAULT_PASS_PERCENT)
    max_attempts = models.PositiveIntegerField(default=MIN_ATTEMPTS)

    class Meta:
        """Apply timing and numeric bounds even when forms are bypassed."""

        ordering = ("deadline", "pk")
        indexes = [models.Index(fields=["deadline", "id"], name="quiz_deadline_pk_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(deadline__gt=models.F("opens_at")),
                name="questionnaire_window_ordered",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    duration_minutes__gte=MIN_DURATION_MINUTES,
                    duration_minutes__lte=MAX_DURATION_MINUTES,
                ),
                name="questionnaire_duration_bounds",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    pass_percent__gte=MIN_PASS_PERCENT,
                    pass_percent__lte=MAX_PASS_PERCENT,
                ),
                name="questionnaire_pass_bounds",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    max_attempts__gte=MIN_ATTEMPTS, max_attempts__lte=MAX_ATTEMPTS
                ),
                name="questionnaire_attempt_bounds",
            ),
        ]

    def __str__(self) -> str:
        """Give authoring choices a recognizable label."""
        return self.title


class Question(TimeStampedModel):
    """Retain marked question history once attempts have been created."""

    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.PROTECT, related_name="questions"
    )
    text = models.TextField()
    order = models.PositiveIntegerField()
    marks = models.PositiveIntegerField(default=MIN_MARKS)

    class Meta:
        """Keep question ordering and positive marks valid under direct writes."""

        ordering = ("order", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("questionnaire", "order"), name="unique_questionnaire_order"
            ),
            models.CheckConstraint(
                condition=models.Q(order__gte=FIRST_QUESTION_ORDER),
                name="question_order_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(marks__gte=MIN_MARKS), name="question_marks_positive"
            ),
        ]


class Option(TimeStampedModel):
    """Keep answer choices immutable references for submitted answers."""

    question = models.ForeignKey(
        Question, on_delete=models.PROTECT, related_name="options"
    )
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        """Let the database enforce the at-most-one half of exact correctness."""

        ordering = ("pk",)
        constraints = [
            models.UniqueConstraint(
                fields=("question",),
                condition=models.Q(is_correct=True),
                name="one_correct_option_at_most",
            )
        ]


class Attempt(TimeStampedModel):
    """Represent a single durable start-to-submission lifecycle."""

    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.PROTECT, related_name="attempts"
    )
    trainee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assessment_attempts",
    )
    started_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    percent = models.DecimalField(max_digits=5, decimal_places=2, default=ZERO_PERCENT)
    passed = models.BooleanField(default=False)
    status = models.CharField(
        max_length=max(map(len, AttemptStatus.values)),
        choices=AttemptStatus.choices,
        default=AttemptStatus.IN_PROGRESS,
    )

    class Meta:
        """Bound grades and prevent concurrent open attempts for the same quiz."""

        ordering = ("pk",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    percent__gte=ZERO_PERCENT, percent__lte=MAX_PASS_PERCENT
                ),
                name="attempt_percent_bounds",
            ),
            models.UniqueConstraint(
                fields=("questionnaire", "trainee"),
                condition=models.Q(status=AttemptStatus.IN_PROGRESS),
                name="one_open_attempt",
            ),
        ]


class AttemptAnswer(TimeStampedModel):
    """Store only answered questions with database-derived correctness."""

    attempt = models.ForeignKey(
        Attempt, on_delete=models.PROTECT, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.PROTECT, related_name="attempt_answers"
    )
    selected_option = models.ForeignKey(
        Option, on_delete=models.PROTECT, related_name="attempt_answers"
    )
    is_correct = models.BooleanField()

    class Meta:
        """Prevent duplicate answer rows on repeated submission."""

        constraints = [
            models.UniqueConstraint(
                fields=("attempt", "question"), name="unique_attempt_question"
            )
        ]
