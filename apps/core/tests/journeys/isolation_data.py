"""Create both sides of an isolation journey entirely through HTTP workflows."""

from apps.announcements.models import Announcement
from apps.certificates.models import Certificate
from apps.competency.models import TrainerCompetency
from apps.core import clock
from apps.core.demo_files import demo_pdf, demo_png
from apps.core.tests.journeys.helpers import (
    learning_course,
    post,
    questionnaire,
    signup,
)
from apps.core.tests.journeys.test_happy_path import _learn
from apps.courses.models import Enrollment
from apps.feedback.models import Feedback
from apps.library.models import LibraryResource
from apps.profiles.models import ExternalCertificate, Qualification, WorkExperience


def owner_bundle(journey: tuple) -> dict:
    """Populate real, readable target IDs instead of testing against absent objects."""
    admin, trainer, staff, trainee, learner, subject = journey
    course, modules = learning_course(staff, subject.pk)
    quiz, question = questionnaire(staff, course)
    _learn(learner, course, modules, (quiz, question))
    bundle = _identity(journey)
    bundle.update(course=course, module=modules[0], quiz=quiz, question=question)
    bundle.update(
        enrollment=Enrollment.objects.get(course=course),
        attempt=quiz.attempts.get(),
        award=Certificate.objects.get(enrollment__course=course),
    )
    _profiles(bundle)
    _content(bundle)
    return bundle


def second_journey(journey: tuple) -> tuple:
    """Create the second trainer and trainee through signup and approval HTTP."""
    admin, _, _, _, _, subject = journey
    trainer, staff = signup(admin, "vikram", "TRAINER")
    trainee, learner = signup(admin, "diya")
    return admin, trainer, staff, trainee, learner, subject


def _profiles(bundle: dict) -> None:
    """Attach private history and files to both real role profiles."""
    post(
        bundle["staff"],
        "profiles:trainer_edit",
        {"years_experience": 3, "photo": demo_png()},
    )
    post(
        bundle["learner"],
        "profiles:trainee_edit",
        {"bio": "Private history", "photo": demo_png()},
    )
    bundle.update(
        trainer_profile=bundle["trainer"].trainer_profile,
        trainee_profile=bundle["trainee"].trainee_profile,
    )
    _children(bundle)


def _children(bundle: dict) -> None:
    """Use validated child forms for real qualifications, dates and file evidence."""
    profile = bundle["trainee_profile"]
    specs = (
        ("qualification", Qualification, qualification_data()),
        ("experience", WorkExperience, experience_data()),
        ("certificate", ExternalCertificate, certificate_data()),
    )
    for slug, model, data in specs:
        post(bundle["learner"], f"profiles:{slug}_create", data)
        bundle[slug] = model.objects.get(profile=profile)


def qualification_data() -> dict:
    """Keep education form input valid at the patched local date."""
    return {
        "degree": "Data diploma",
        "institution": "Pragati",
        "year": clock.today().year,
    }


def experience_data() -> dict:
    """Exercise ongoing employment through the same date validation as real users."""
    return {
        "organisation": "Pragati",
        "role": "Analyst",
        "start_date": clock.today().isoformat(),
    }


def certificate_data() -> dict:
    """Upload a valid PDF rather than assigning a synthetic database path."""
    return {
        "title": "Private evidence",
        "issuer": "Pragati",
        "file": demo_pdf(),
        "issued_on": clock.today().isoformat(),
    }


def _identity(journey: tuple) -> dict:
    """Keep both real user/client pairs together without positional ambiguity."""
    keys = ("admin", "trainer", "staff", "trainee", "learner", "subject")
    return dict(zip(keys, journey, strict=True))


def _content(bundle: dict) -> None:
    """Collect independently authored resources, feedback and declarations."""
    _resource(bundle)
    _declarations(bundle)
    course = bundle["course"]
    post(
        bundle["learner"],
        "feedback:course_submit",
        {"rating": 5, "comment": "Private comment"},
        (course.pk,),
    )
    bundle.update(
        feedback=Feedback.objects.get(course=course), skill=course.subject.skills.get()
    )


def _resource(bundle: dict) -> None:
    """Publish one owner's real PDF for shared reads and restricted management."""
    course, staff = bundle["course"], bundle["staff"]
    post(
        staff,
        "library:create",
        {
            "title": f"Private workbook {course.pk}",
            "subject": course.subject_id,
            "course": course.pk,
            "kind": "DOCUMENT",
            "file": demo_pdf(),
        },
    )
    resource = LibraryResource.objects.get(course=course)
    post(staff, "library:publish", args=(resource.pk,))
    bundle["resource"] = resource


def _declarations(bundle: dict) -> None:
    """Make ownership and administrative denials target actual existing rows."""
    course = bundle["course"]
    post(
        bundle["staff"],
        "competency:add",
        {
            "subject": course.subject_id,
            "proficiency": 4,
            "years_experience": 3,
        },
    )
    post(
        bundle["admin"],
        "announcements:create",
        {
            "title": f"Draft {course.pk}",
            "body": "Draft",
            "category": "NOTICE",
        },
    )
    bundle.update(
        competency=TrainerCompetency.objects.get(trainer=bundle["trainer"]),
        announcement=Announcement.objects.get(title=f"Draft {course.pk}"),
    )
