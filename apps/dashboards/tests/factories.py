"""Build a deterministic fake analytics dataset with retained and retaken history."""

from apps.accounts.tests.factories import UserFactory
from apps.assessments.tests.factories import AttemptFactory, QuestionnaireFactory
from apps.catalog.tests.factories import SubjectFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.courses.tests.factories import CourseFactory, EnrollmentFactory
from apps.feedback.tests.factories import FeedbackFactory


def analytics_dataset() -> dict:
    """Seed exact counts without creating a seed command or persistent records."""
    admin = UserFactory(active_admin=True)
    trainer, other = UserFactory.create_batch(2, approved_trainer=True)
    a, b, c = UserFactory.create_batch(3, approved_trainee=True)
    UserFactory(pending_trainee=True)
    UserFactory(rejected_user=True)
    subject = SubjectFactory(name="Data Skills")
    zero = SubjectFactory(name="Zero Enrollments")
    first, second, foreign = analytics_courses(trainer, other, (subject, zero))
    active = analytics_enrollments((first, second), (a, b, c))
    quizzes = [
        QuestionnaireFactory(course=course) for course in (first, second, foreign)
    ]
    populate_analytics(quizzes, (a, b, c), (first, second))
    return {
        "admin": admin,
        "trainer": trainer,
        "other": other,
        "active": active,
        "subject": subject,
        "zero": zero,
        "quizzes": quizzes,
    }


def populate_analytics(quizzes: list, trainees: tuple, courses: tuple) -> None:
    """Keep retake and dropped-only attempts distinct from the participation cohort."""
    a, b, c = trainees
    for trainee, percent in ((a, 40), (a, 80), (b, 100), (c, 20)):
        AttemptFactory(
            questionnaire=quizzes[0],
            trainee=trainee,
            status="SUBMITTED",
            percent=percent,
            passed=percent >= 50,
        )
    AttemptFactory(questionnaire=quizzes[1], trainee=a, status="TIMED_OUT")
    for author, course, rating in (
        (a, courses[0], 4),
        (b, courses[0], 5),
        (a, courses[1], 2),
    ):
        FeedbackFactory(author=author, course=course, rating=rating)


def analytics_courses(trainer: object, other: object, subjects: tuple) -> tuple:
    """Create own published/draft courses and one unrelated published course."""
    subject, zero = subjects
    first = CourseFactory(
        trainer=trainer, subject=subject, is_published=True, title="Published own"
    )
    second = CourseFactory(
        trainer=trainer, subject=subject, is_published=False, title="Draft own"
    )
    foreign = CourseFactory(
        trainer=other, subject=zero, is_published=True, title="Other trainer course"
    )
    return first, second, foreign


def analytics_enrollments(courses: tuple, trainees: tuple) -> object:
    """Keep repeated trainee enrollment distinct from dropped history."""
    first, second = courses
    a, b, c = trainees
    active = EnrollmentFactory(course=first, trainee=a)
    completed = EnrollmentFactory(course=first, trainee=b, status="COMPLETED")
    EnrollmentFactory(course=first, trainee=c, status="DROPPED")
    EnrollmentFactory(course=second, trainee=a)
    CertificateFactory(enrollment=completed, grade="A")
    return active
