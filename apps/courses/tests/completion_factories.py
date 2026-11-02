"""Build ready completion scenarios without triggering writes prematurely."""

from apps.assessments import services
from apps.assessments.tests.factories import ready_quiz
from apps.courses.models import Enrollment
from apps.courses.tests.factories import ModuleFactory


def completion_flow() -> tuple:
    """Give tests one ready quiz, active enrollment and unfinished module."""
    quiz, question, trainee = ready_quiz(max_attempts=2)
    enrollment = Enrollment.objects.get(course=quiz.course, trainee=trainee)
    module = ModuleFactory(course=quiz.course, order=1)
    return enrollment, module, quiz, question


def pass_quiz(enrollment: object, quiz: object, question: object) -> object:
    """Use the real timed grading service so the passing trigger is exercised."""
    attempt = services.start_attempt(enrollment.trainee, quiz)
    return services.submit_attempt(
        enrollment.trainee, attempt, {question.pk: question.options.first().pk}
    )
