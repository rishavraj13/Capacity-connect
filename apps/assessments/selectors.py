"""Preserve assessment read imports while concern-specific modules own queries."""

from apps.assessments.attempt_selectors import (
    best_submitted_percents as best_submitted_percents,
)
from apps.assessments.attempt_selectors import (
    completion_questionnaires as completion_questionnaires,
)
from apps.assessments.attempt_selectors import has_passed as has_passed
from apps.assessments.attempt_selectors import history_for as history_for
from apps.assessments.attempt_selectors import owned_attempts as owned_attempts
from apps.assessments.attempt_selectors import (
    passed_questionnaire_ids as passed_questionnaire_ids,
)
from apps.assessments.attempt_selectors import result_history as result_history
from apps.assessments.authoring_selectors import authoring_detail as authoring_detail
from apps.assessments.authoring_selectors import (
    conflicting_course_questionnaire_subjects as _subject_conflicts,
)
from apps.assessments.authoring_selectors import (
    managed_questionnaires as managed_questionnaires,
)
from apps.assessments.authoring_selectors import managed_questions as managed_questions
from apps.assessments.authoring_selectors import question_initial as question_initial
from apps.assessments.authoring_selectors import (
    questionnaires_for_course as questionnaires_for_course,
)
from apps.assessments.paper_selectors import paper_for as paper_for
from apps.assessments.participation_selectors import participation as participation
from apps.assessments.result_selectors import attempt_result as attempt_result
from apps.assessments.usage_selectors import next_deadlines_for as next_deadlines_for
from apps.assessments.usage_selectors import (
    startable_questionnaires as startable_questionnaires,
)
from apps.assessments.usage_selectors import (
    trainee_questionnaires as trainee_questionnaires,
)

conflicting_course_questionnaire_subjects = _subject_conflicts
